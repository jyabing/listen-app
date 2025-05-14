from django.contrib import admin, messages
from .models import Category, Material, AnswerRecord
from .utils import generate_tts
import time

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('id', 'question_text', 'language', 'created_at', 'auto_audio_generated')
    search_fields = ('question_text', 'answer_text')
    list_filter = ('categories', 'language')
    filter_horizontal = ('categories',)
    readonly_fields = ('auto_audio_generated',)  # 防止手动修改

    def save_model(self, request, obj, form, change):
        # 如果没有上传音频，尝试自动生成
        if not obj.audio and obj.question_text:
            filename = f"auto_{int(time.time())}_{obj.id or 'new'}.mp3"
            try:
                relative_path = generate_tts(
                    text=obj.question_text,
                    lang_code=obj.language,
                    filename=filename
                )
                obj.audio.name = relative_path
                obj.auto_audio_generated = True
                self.message_user(request, f"✅ 音频已成功生成: {filename}", messages.SUCCESS)
            except Exception as e:
                self.message_user(request, f"❌ 音频生成失败: {e}", messages.ERROR)

        super().save_model(request, obj, form, change)

@admin.register(AnswerRecord)
class AnswerRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'material', 'is_correct', 'answered_at')
    list_filter = ('is_correct', 'answered_at')
