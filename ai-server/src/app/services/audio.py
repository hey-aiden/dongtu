import tempfile
from pathlib import Path

from app.llm import bailian_audio_text_file, bailian_text_audio


def transform_text_audio(prompt: str) -> str:
    audio_url = bailian_text_audio(prompt=prompt)
    return {"audio_url": audio_url}


def transform_audio_text(file) -> str:
    """把上传的音频文件转写为文本。"""
    suffix = Path(file.filename or "audio.wav").suffix  # 如 ".wav"
    fmt = suffix.lstrip(".").lower()
    # 先落临时文件,转写完成后删除
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(file.file.read())
        tmp_path = tmp.name
    try:
        text = bailian_audio_text_file(tmp_path, format=fmt)
    finally:
        Path(tmp_path).unlink(missing_ok=True)
    return {"content": text}
