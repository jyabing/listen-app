import os
from gtts import gTTS
from django.conf import settings
from datetime import timedelta
from django.utils import timezone


def generate_tts(text, lang_code="ja", filename="output.mp3"):
    """
    使用 gTTS 将文本转为音频（MP3），保存到 media/audio/ 目录下。
    
    参数：
        text: 要朗读的文字内容（支持多语言）
        lang_code: 语言代码（如 'ja' 日语, 'en' 英语）
        filename: 保存的文件名（相对路径）
    
    返回：
        FileField 可接受的相对路径，如 'audio/xxx.mp3'
    """
    if not text.strip():
        raise ValueError("TTS 生成失败：文本不能为空。")

    # 构造完整的音频存储路径
    audio_dir = os.path.join(settings.MEDIA_ROOT, 'audio')
    os.makedirs(audio_dir, exist_ok=True)

    audio_path = os.path.join(audio_dir, filename)

    # 创建并保存 TTS 音频
    try:
        tts = gTTS(text=text, lang=lang_code)
        tts.save(audio_path)
    except Exception as e:
        raise RuntimeError(f"TTS 生成失败: {e}")

    return f'audio/{filename}'  # 相对路径（用于 FileField）

def sm2_update(record, quality):
    """
    对一个 AnswerRecord 应用 SM-2 算法，
    quality: 0–5 分，>=3 视为“学会”
    """
    # 如果答题质量 < 3，则重置重复次数
    if quality < 3:
        record.repetitions = 0
        record.interval = 1
    else:
        # 计算新的难度系数
        new_ease = record.ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        record.ease = max(new_ease, 1.3)

        record.repetitions += 1
        # 第一次复习间隔 1 天，第二次 6 天，其后按 formula
        if record.repetitions == 1:
            record.interval = 1
        elif record.repetitions == 2:
            record.interval = 6
        else:
            record.interval = int(record.interval * record.ease)

    # 计算下次复习日期
    record.next_review = timezone.now().date() + timedelta(days=record.interval)
    record.save()
    return record