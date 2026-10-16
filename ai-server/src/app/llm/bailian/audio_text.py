"""阿里云百炼语音转文本(录音文件转写 + 实时识别)"""

import json
from http import HTTPStatus
from urllib import request
from urllib.parse import urlparse

import dashscope
from app.config import settings
from dashscope.audio.asr import Recognition, RecognitionCallback, Transcription

dashscope.api_key = settings.dashscope_api_key
# 录音文件转写(filetrans)走 HTTP 协议,需要指向 MaaS 的 /api/v1 端点。
# .env 里 HOST_DASHSCOPE 存的是 compatible-mode 地址(/compatible-mode/v1),
# 这里取同一主机拼出 /api/v1 基础地址。
dashscope.base_http_api_url = f"https://{urlparse(settings.host_dashscope).netloc}/api/v1"
# 实时识别走 WebSocket 协议,复用 MaaS 的 WebSocket 端点
dashscope.base_websocket_api_url = settings.host_websocket_dashscope

model = "qwen-audio-3.1-asr-flash-filetrans"
language_hints = ["zh", "en"]

# 实时识别模型:直接读本地文件转写,无需先上传到公网 URL
model_realtime = "paraformer-realtime-v2"


def bailian_audio_text(audio_url: str) -> str:
    """把音频文件(公网 URL)转写为文本。

    Args:
        audio_url: 待转写音频的可访问 URL(需先上传到 OSS 等公网可读地址)。

    Returns:
        识别出的完整文本;转写失败时抛出 RuntimeError。
    """
    task_response = Transcription.async_call(
        model=model,
        file_urls=[audio_url],
        language_hints=language_hints,
    )

    transcription_response = Transcription.wait(task=task_response.output.task_id)
    if transcription_response.status_code != HTTPStatus.OK:
        raise RuntimeError(f"语音转写失败: {transcription_response.message}")

    # 单个音频文件对应一条结果;subtask_status 为 SUCCEEDED 才表示转写成功
    for transcription in transcription_response.output.get("results", []):
        if transcription["subtask_status"] != "SUCCEEDED":
            raise RuntimeError(f"语音转写失败: {transcription}")

        result = json.loads(
            request.urlopen(transcription["transcription_url"]).read().decode("utf8")
        )
        # transcripts 按声道分组(单声道仅一条),合并所有声道的 text
        return "".join(item["text"] for item in result.get("transcripts", []))

    raise RuntimeError("语音转写结果为空")


def bailian_audio_text_file(file_path: str, format: str, sample_rate: int = 16000) -> str:
    """把本地音频文件直接转写为文本(实时识别,无需公网 URL)。

    Args:
        file_path: 本地音频文件路径。
        format: 音频格式,如 wav/mp3/pcm 等。
        sample_rate: 采样率。paraformer-realtime-v2 支持任意采样率。

    Returns:
        识别出的完整文本;转写失败时抛出 RuntimeError。
    """
    recognition = Recognition(
        model=model_realtime,
        callback=RecognitionCallback(),
        format=format,
        sample_rate=sample_rate,
    )
    result = recognition.call(file=file_path)
    if result.status_code != HTTPStatus.OK:
        raise RuntimeError(f"语音转写失败: {result.message}")

    sentence = result.get_sentence()
    if isinstance(sentence, dict):
        return sentence.get("text", "")
    if not sentence:
        raise RuntimeError("语音转写结果为空")
    return "".join(s.get("text", "") for s in sentence)
