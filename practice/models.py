from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Material(models.Model):
    question_text = models.TextField(verbose_name="题目文本")
    answer_text = models.TextField(verbose_name="标准答案")
    audio = models.FileField(upload_to='audio/', null=True, blank=True)
    categories = models.ManyToManyField(Category)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question_text[:30]  # 显示前30个字符

class AnswerRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    user_answer = models.TextField()
    is_correct = models.BooleanField(default=False)
    answered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.material.id}"
    