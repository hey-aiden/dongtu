"""
阿里云百炼llm
"""

from datetime import datetime, timezone
from pathlib import Path

import dashscope
from app.config import settings
from dashscope.audio.tts_v2 import *

dashscope.api_key = settings.dashscope_api_key
dashscope.base_websocket_api_url = settings.host_websocket_dashscope


model = "qwen-audio-3.0-tts-flash"
voice = "longanlingxi"


def bailian_text_audio(prompt: str) -> str:
    synthesizer = SpeechSynthesizer(model=model, voice=voice)
    audio = synthesizer.call(prompt)
    # 首次发送文本时需建立 WebSocket 连接，因此首包延迟会包含连接建立的耗时
    print(
        f"[Metric] requestId为：{synthesizer.get_last_request_id()}，首包延迟为：{synthesizer.get_first_package_delay()}毫秒"
    )
    # 将音频保存至本地
    audio_dir = Path("output")
    audio_dir.mkdir(exist_ok=True)

    filename = f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')}.mp3"
    audio_file = audio_dir / filename

    with open(audio_file, "wb") as f:
        f.write(audio)

    return str(audio_file)
