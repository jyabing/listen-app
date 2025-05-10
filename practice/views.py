import random
from django.shortcuts import render, redirect
from .models import Material, AnswerRecord
from django.contrib.auth.decorators import login_required
from django.utils import timezone

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
