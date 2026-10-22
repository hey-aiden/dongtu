import base64
from http import HTTPStatus
from pathlib import Path
from urllib.parse import urlparse

import dashscope
from app.config import settings
from app.utils import log_info
from dashscope import MultiModalConversation

dashscope.api_key = settings.dashscope_api_key

# .env 里 HOST_DASHSCOPE 存的是 compatible-mode 地址(/compatible-mode/v1),
# 语音识别(qwen-audio-3.0-asr-flash)走 MaaS 原生 /api/v1 端点,需取同一主机拼出 /api/v1 基础地址。
dashscope.base_http_api_url = (
    f"https://{urlparse(settings.host_dashscope).netloc}/api/v1"
)

# 文件后缀 -> data URI 的 MIME 类型。format 参数直接取后缀去掉点号(如 "wav")。
_AUDIO_MIME = {
    "wav": "audio/wav",
    "mp3": "audio/mpeg",
    "m4a": "audio/mp4",
    "aac": "audio/aac",
    "opus": "audio/opus",
    "ogg": "audio/ogg",
    "flac": "audio/flac",
    "webm": "audio/webm",
    "pcm": "audio/pcm",
}


def bailian_audio_text_file(local_file_path: str) -> str:
    """使用 qwen-audio-3.0-asr-flash 模型进行同步语音识别（本地文件走 base64 data URI）。

    同步接口要求 parameters.format 必填,且本地文件不能直接传 file:// 路径,
    需 base64 编码成 data:<mime>;base64,... 形式(≤10MB,建议短音频 ≤5 分钟)。
    """
    fmt = Path(local_file_path).suffix.lstrip(".").lower()  # 拿到音频格式后缀
    print("fmt: ", fmt)
    mime = _AUDIO_MIME.get(fmt, f"audio/{fmt}")

    with open(local_file_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    data_uri = f"data:{mime};base64,{b64}"

    log_info(
        f"调用 qwen-audio-3.0-asr-flash 模型进行语音转写, format={fmt}",
        "audio_temp",
    )

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "input_audio", "input_audio": {"data": data_uri}},
            ],
        }
    ]

    response = MultiModalConversation.call(
        model="qwen-audio-3.0-asr-flash", messages=messages, format=fmt
    )

    if response.status_code == HTTPStatus.OK:
        # 同步 ASR 响应文本在 output.text,无 choices 字段
        return response.output.text
    else:
        raise RuntimeError(f"语音转写失败: {response.code} - {response.message}")
