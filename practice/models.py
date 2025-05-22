from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

LANG_CHOICES = [
    ('ja', '日语'),
    ('en', '英语'),
    ('zh-CN', '中文'),
]

class Material(models.Model):
    question_text = models.TextField(verbose_name="听力文本")
    answer_text = models.TextField(verbose_name="标准答案")
    translation_ja = models.TextField("日文翻译", blank=True)
    translation_en = models.TextField("英文翻译", blank=True)
    translation_zh = models.TextField("中文翻译", blank=True)

    language = models.CharField(
        max_length=10,
        choices=LANG_CHOICES,
        default='ja',
        verbose_name="朗读语言"
    )

    audio = models.FileField(upload_to='audio/', null=True, blank=True)
    auto_audio_generated = models.BooleanField(default=False)

    categories = models.ManyToManyField(Category)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question_text[:30]# 显示前30个字符

class AnswerRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    user_answer = models.TextField()
    is_correct = models.BooleanField(default=False)
    answered_at = models.DateTimeField(auto_now_add=True)

    # —— 以下为 SM-2 算法所需字段 ——
    repetitions = models.IntegerField(default=0)
    interval = models.IntegerField(default=0)               # 天数
    ease = models.FloatField(default=2.5)                    # 难度系数
    next_review = models.DateField(null=True, blank=True)    # 下次复习日期

    def __str__(self):
        return f"{self.user.username} – {self.material.id}"

class PracticeSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.started_at.strftime('%Y-%m-%d %H:%M')}"


class OralAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    material = models.ForeignKey('Material', on_delete=models.CASCADE)
    session = models.ForeignKey('practice.PracticeSession', on_delete=models.CASCADE)
    audio_file = models.FileField(upload_to='oral/')
    recognized_text = models.TextField(blank=True)
    is_correct = models.BooleanField(default=False)
    keyword_hits = models.IntegerField(default=0)
    keyword_total = models.IntegerField(default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.material.question_text[:30]}"