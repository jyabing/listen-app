import random, math, os, whisper,html
from django.shortcuts import render, redirect, get_object_or_404
from .models import Material, AnswerRecord, Category, PracticeSession, OralAnswer
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from datetime import date
from django.db.models import Max, Count, F
from .utils import sm2_update, transcribe_and_score, highlight_diff, is_answer_similar
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

model = whisper.load_model("base")  # 推荐全局加载一次

def home_view(request):
    """
    入口首页：展示各个功能入口链接
    """
    today_due_count = 0
    if request.user.is_authenticated:
        today = timezone.now().date()
        today_due_count = AnswerRecord.objects.filter(
            user=request.user,
            next_review__lte=today
        ).values('material').distinct().count()

    return render(request, 'home.html', {
        'today_due_count': today_due_count
    })

@csrf_exempt
def process_oral_answer(request, session_id, material_id):
    if request.method == 'POST' and request.FILES.get('audio'):
        session = get_object_or_404(PracticeSession, id=session_id)
        material = get_object_or_404(Material, id=material_id)
        audio_file = request.FILES['audio']

        # 保存音频文件
        oral_answer = OralAnswer.objects.create(
            user=request.user,
            session=session,
            material=material,
            audio_file=audio_file
        )

        # 语音识别
        result = model.transcribe(oral_answer.audio_file.path)
        recognized = result["text"].strip()

        # 比对
        correct_answer = material.answer_text.strip()
        is_correct = recognized.lower() == correct_answer.lower()

        oral_answer.recognized_text = recognized
        oral_answer.is_correct = is_correct
        oral_answer.save()

        return JsonResponse({
            "recognized_text": recognized,
            "is_correct": is_correct
        })
    return JsonResponse({"error": "Invalid request"}, status=400)

def logout_view(request):
    logout(request)
    messages.success(request, "你已成功登出。欢迎随时回来继续练习！")
    return redirect('home')

def is_answer_similar(user_input, correct_answer, threshold=0.85):
    """
    使用 difflib 比较相似度，threshold=0.85 表示相似度达到 85% 即视为正确。
    """
    return difflib.SequenceMatcher(None, user_input.lower().strip(), correct_answer.lower().strip()).ratio() >= threshold

def highlight_diff(user_input, correct_answer):
    """
    返回带 <mark> 标签的对比文本，高亮显示用户错误部分。
    """
    matcher = difflib.SequenceMatcher(None, correct_answer.strip(), user_input.strip())
    result = []
    for opcode, i1, i2, j1, j2 in matcher.get_opcodes():
        correct_part = html.escape(correct_answer[i1:i2])
        user_part = html.escape(user_input[j1:j2])
        if opcode == 'equal':
            result.append(user_part)
        elif opcode == 'replace' or opcode == 'delete':
            result.append(f"<mark>{user_part}</mark>")
        elif opcode == 'insert':
            result.append(f"<mark>{user_part}</mark>")
    return ''.join(result)

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            next_url = request.GET.get("next") or "home"  # ✅ 优先跳转 next，否则回首页
            return redirect(next_url)
        else:
            messages.error(request, "用户名或密码错误")

    return render(request, "practice/login.html")

@login_required
def practice_view(request):
    # 获取分类、模式参数
    category_id = request.GET.get("category_id")
    mode = request.GET.get("mode", "typing")

    # 如果没有选分类，跳回设置页
    if not category_id:
        return redirect("practice_setup")

    # 验证 category_id
    try:
        category_id = int(category_id)
    except ValueError:
        return redirect("practice_setup")

    # 随机选题
    materials = Material.objects.filter(categories__id=category_id)
    if not materials.exists():
        return render(request, "practice/result.html", {
            "material": None,
            "message": "该分类下暂无题目，请返回选择其他分类。"
        })
    material = random.choice(materials)

    # 处理 POST（用户提交答案）
    if request.method == "POST" and mode == "speaking":
        uploaded = request.FILES.get("audio_data")
        if not uploaded:
            return render(request, "practice/result.html", {
                "material": material,
                "user_answer": "未检测到录音",
                "is_correct": False,
            })

        # 1) 保存音频文件到 media/user_audio/...
        rel_path = f"user_audio/{request.user.username}_{timezone.now().timestamp()}.webm"
        full_path = os.path.join(settings.MEDIA_ROOT, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb+") as f:
            for chunk in uploaded.chunks():
                f.write(chunk)

        # 2) 转写并判分
        transcript = transcribe_audio(full_path)
        correct = material.answer_text.strip()
        is_corr = is_answer_similar(transcript, correct, threshold=0.8)
        highlighted = highlight_diff(transcript, correct)

        # 3) 保存记录（先记录原始转写和对错）
        rec = AnswerRecord.objects.create(
            user=request.user,
            material=material,
            user_answer=transcript,
            is_correct=is_corr,
            answered_at=timezone.now()
        )
        # 可选：结合 SM-2 更新复习计划
        # quality = 5 if is_corr else 2
        # sm2_update(rec, quality)

        # 4) 渲染结果页面
        return render(request, "practice/result.html", {
            "material": material,
            "mode": mode,
            "transcript": transcript,
            "highlighted": highlighted,
            "is_correct": is_corr,
            "audio_path": f"/media/{rel_path}"
        })

@login_required
def practice_setup_view(request):
    categories = Category.objects.all()
    return render(request, "practice/setup.html", {"categories": categories})

@login_required
def practice_view(request):
    category_id = request.GET.get("category_id")
    mode = request.GET.get("mode", "typing")

    if not category_id:
        return redirect("practice_setup")

    try:
        category_id = int(category_id)
    except ValueError:
        return redirect("practice_setup")

    materials = Material.objects.filter(categories__id=category_id)
    if not materials.exists():
        return render(request, "practice/result.html", {
            "material": None,
            "message": "该分类下暂无题目，请返回选择其他分类。"
        })

    material = random.choice(materials)

    if request.method == "POST":
        if mode == "speaking":
            uploaded_file = request.FILES.get("audio_data")
            if uploaded_file:
                # 保存音频文件
                filepath = f"user_audio/{request.user.username}_{timezone.now().timestamp()}.webm"
                full_path = os.path.join(settings.MEDIA_ROOT, filepath)
                
                with open(f"media/{filepath}", 'wb+') as f:
                    for chunk in uploaded_file.chunks():
                        f.write(chunk)
                # 语音识别（调用 Whisper）
                model = whisper.load_model("base")  # 也可以用 "tiny"、"small" 等
                result = model.transcribe(full_path)
                transcribed_text = result["text"].strip()

                # 与标准答案比较（你可以决定是否忽略大小写等）
                is_correct = is_answer_similar(transcribed_text, material.answer_text)

                # ✅ 在这里加入高亮生成！
                highlighted = highlight_diff(transcribed_text, material.answer_text)

                # 保存答题记录
                AnswerRecord.objects.create(
                    user=request.user,
                    material=material,
                    user_answer=f"[语音提交: {filepath}]",
                    is_correct=False,
                    answered_at=timezone.now()
                )
                quality = 5 if is_correct else 2
                sm2_update(rec, quality)

                return render(request, "practice/result.html", {
                    "material": material,
                    "user_answer": "已上传录音",
                    "is_correct": False,
                    "audio_path": f"/media/{filepath}"
                })

            return render(request, "practice/result.html", {
                "material": material,
                "user_answer": "未检测到录音",
                "is_correct": False
            })

        else:
            user_answer = request.POST.get("user_answer", "").strip()
            is_correct = user_answer == material.answer_text.strip()

            AnswerRecord.objects.create(
                user=request.user,
                material=material,
                user_answer=user_answer,
                is_correct=is_correct,
                answered_at=timezone.now()
            )

            return render(request, "practice/result.html", {
                "material": material,
                "user_answer": user_answer,
                "is_correct": is_correct
            })

    # 最后：如果是 GET 请求，渲染练习页
    if mode == "speaking":
        return render(request, "practice/practice_speaking.html", {
            "material": material,
            "mode": mode
        })
    else:
        return render(request, "practice/practice.html", {
            "material": material,
            "mode": mode
        })

@login_required
def wrong_list_view(request):
    # 获取当前用户答错过的题（只保留每题最后一次答错记录）
    wrong_records = (
        AnswerRecord.objects.filter(user=request.user, is_correct=False)
        .values("material")
        .annotate(latest=Max("answered_at"))
        .order_by("-latest")
    )

    material_ids = [item["material"] for item in wrong_records]
    materials = Material.objects.filter(id__in=material_ids)

    return render(request, "practice/wrong_list.html", {
        "materials": materials
    })

@login_required
def retry_wrong_view(request, material_id):
    try:
        material = Material.objects.get(id=material_id)
    except Material.DoesNotExist:
        return redirect("wrong_list")

    mode = request.GET.get("mode", "typing")

    if request.method == "POST":
        if mode == "speaking":
            # 和前面口说模式逻辑一致
            ...
        else:
            user_answer = request.POST.get("user_answer", "").strip()
            is_correct = is_answer_similar(user_answer, material.answer_text)
            highlighted = highlight_diff(user_answer, material.answer_text)

            AnswerRecord.objects.create(
                user=request.user,
                material=material,
                user_answer=user_answer,
                is_correct=is_correct,
                answered_at=timezone.now()
            )
            quality = 5 if is_correct else 2
            sm2_update(rec, quality)

            return render(request, "practice/result.html", {
                "material": material,
                "user_answer": user_answer,
                "is_correct": is_correct,
                "highlighted": highlighted
            })

    if mode == "speaking":
        return render(request, "practice/practice_speaking.html", {
            "material": material,
            "mode": mode
        })
    else:
        return render(request, "practice/practice.html", {
            "material": material,
            "mode": mode
        })

@login_required
def review_view(request):
    today = timezone.now().date()
    # 筛选出所有 next_review <= 今天 的记录
    due_records = AnswerRecord.objects.filter(
        user=request.user,
        next_review__lte=today
    ).order_by('next_review')
    # 对应的题目列表（按 due 排序）
    materials = [rec.material for rec in due_records]
    return render(request, "practice/review.html", {
        "records": due_records,
        "materials": materials
    })

@login_required
def reading_view(request, mode):
    # 1) 选分类
    cat = request.GET.get("category_id")
    if not cat:
        return redirect("practice_setup")
    try: cat = int(cat)
    except: return redirect("practice_setup")

    qs = Material.objects.filter(categories__id=cat)
    if not qs.exists():
        return render(request, "practice/result.html", {
            "material": None, "message": "暂无题目"
        })
    material = random.choice(qs)

    # 2) 准备选项
    if mode == "translate":
        # 以中文翻译为例，选出 3 个干扰项
        correct = material.translation_zh
        distractors = list(
            Material.objects
                .exclude(id=material.id)
                .values_list("translation_zh", flat=True)
                [:3]
        )
        options = [correct] + distractors
        random.shuffle(options)

    elif mode == "ordering":
        # 将标准答案按空格拆成块
        correct_order = material.answer_text.split()
        options = correct_order[:]  # copy
        random.shuffle(options)
    else:
        return redirect("practice_setup")

    # 3) 处理提交
    if request.method == "POST":
        if mode == "translate":
            choice = request.POST.get("choice")
            is_correct = (choice == correct)
        else:  # ordering
            order = request.POST.getlist("order[]")
            is_correct = (order == correct_order)
            choice = " ".join(order)

        rec = AnswerRecord.objects.create(
            user=request.user,
            material=material,
            user_answer=choice,
            is_correct=is_correct,
            answered_at=timezone.now()
        )
        # 更新 SM-2
        quality = 5 if is_correct else 2
        sm2_update(rec, quality)

        return render(request, "practice/reading_result.html", {
            "material": material,
            "mode": mode,
            "is_correct": is_correct,
            "user_choice": choice,
            "correct": correct if mode=="translate" else " ".join(correct_order)
        })

    # 4) GET 渲染练习页
    return render(request, "practice/reading.html", {
        "material": material,
        "mode": mode,
        "options": options
    })

@login_required
def review_recommendation_view(request):
    today = timezone.now().date()
    records_due = AnswerRecord.objects.filter(user=request.user, next_review__lte=today).select_related("material")

    return render(request, 'practice/review_recommendation.html', {
        'records_due': records_due,
    })

@login_required
def review_summary_view(request):
    today = timezone.now().date()
    user = request.user

    # 1. 今日推荐复习项目数
    today_due_count = AnswerRecord.objects.filter(
        user=user, next_review__lte=today
    ).values('material').distinct().count()

    # 2. 掌握度分布（只看用户最新记录）
    latest_records = (
        AnswerRecord.objects
        .filter(user=user)
        .order_by('material', '-answered_at')
        .distinct('material')
    )

    ease_data = {
        "熟练（≥2.5）": 0,
        "中等（1.8~2.49）": 0,
        "待加强（<1.8）": 0,
    }

    for rec in latest_records:
        if rec.ease >= 2.5:
            ease_data["熟练（≥2.5）"] += 1
        elif rec.ease >= 1.8:
            ease_data["中等（1.8~2.49）"] += 1
        else:
            ease_data["待加强（<1.8）"] += 1

    # 3. 累计练习次数 Top 5
    top_materials = (
        AnswerRecord.objects
        .filter(user=user)
        .values('material__question_text')
        .annotate(count=Count('id'))
        .order_by('-count')[:5]
    )

    return render(request, 'practice/review_summary.html', {
        'today_due_count': today_due_count,
        'ease_data': ease_data,
        'top_materials': top_materials,
    })

@login_required
def review_priority_view(request):
    today = date.today()
    user = request.user

    records = (
        AnswerRecord.objects
        .filter(user=user)
        .order_by('material', '-answered_at')  # 每题保留最后一条
        .distinct('material')
    )

    # 计算遗忘曲线
    data = []  # ✅ 这一行必须放在循环前！

    labels = []
    retention_data = []

    for rec in records:
        days_since = (today - rec.answered_at.date()).days
        ease = rec.ease or 2.5
        k = 10  # 调节因子

        retention = math.exp(-days_since / (ease * k))
        forgetting = 1 - retention

        label = rec.material.question_text[:20].replace('\n', ' ') + f" ({rec.id})"
        labels.append(label)
        retention_data.append(round(retention * 100, 2))  # 百分比显示

        data.append({
            'record': rec,
            'days_since': days_since,
            'retention': round(retention, 3),
            'forgetting': round(forgetting, 3)
        })

    # 按遗忘率排序后重新构建图表数据（确保图表和表格一致）
    sorted_data = sorted(data, key=lambda x: x['forgetting'], reverse=True)
    labels_sorted = [item['record'].material.question_text[:20].replace('\n', ' ') + f" ({item['record'].id})" for item in sorted_data]
    retention_data_sorted = [round(item['retention'] * 100, 2) for item in sorted_data]

    return render(request, 'practice/review_priority.html', {
        'items': sorted_data,
        'labels': labels_sorted,
        'retention_data': retention_data_sorted
    })