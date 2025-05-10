from django.contrib import admin
from .models import Category, Material, AnswerRecord

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('id', 'question_text', 'created_at')
    search_fields = ('question_text', 'answer_text')
    list_filter = ('categories',)
    filter_horizontal = ('categories',)  # 多对多字段横向筛选器
    ordering = ('-created_at',)

@admin.register(AnswerRecord)
class AnswerRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'material', 'is_correct', 'answered_at')
    list_filter = ('is_correct', 'answered_at')
