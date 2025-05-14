import os
from gtts import gTTS
from django.conf import settings


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
