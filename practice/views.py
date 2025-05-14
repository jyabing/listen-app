import random
from django.shortcuts import render, redirect
from .models import Material, AnswerRecord, Category
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.utils import timezone
import whisper
import os
import difflib
import html
from django.db.models import Max
from .utils import sm2_update

# …在 POST 打字模式逻辑里…
raw = request.POST.get("user_answer", "").strip()
is_correct = raw == material.answer_text.strip()

rec = AnswerRecord.objects.create(
    user=request.user,
    material=material,
    user_answer=raw,
    is_correct=is_correct,
    answered_at=timezone.now(),
    # repetitions, interval, ease 三个初始会用默认值
)
# 根据是否答对赋予 quality 分数
quality = 5 if is_correct else 2
rec = sm2_update(rec, quality)

def home_view(request):
    """
    入口首页：展示各个功能入口链接
    """
    return render(request, 'home.html')

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
            return redirect("practice_setup")  # 登录成功后跳到分类选择页
        else:
            messages.error(request, "用户名或密码错误")

    return render(request, "practice/login.html")

@login_required
def practice_view(request):
    # 获取所有题目，从中随机选择一个
    material = random.choice(Material.objects.all())

    if request.method == "POST":
        user_answer = request.POST.get("user_answer", "").strip()
        is_correct = user_answer == material.answer_text.strip()

        # 保存答题记录
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

    return render(request, "practice/practice.html", {"material": material})

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