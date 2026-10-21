"""
文生图模型调用
"""

from urllib.parse import urlparse

import dashscope
from app.config import settings
from app.utils import log_info
from dashscope import MultiModalConversation

# .env 里 HOST_DASHSCOPE 存的是 compatible-mode 地址(/compatible-mode/v1),
# 文生图(MultiModalConversation)走 MaaS 原生 /api/v1 端点,需取同一主机拼出 /api/v1 基础地址。
dashscope.base_http_api_url = (
    f"https://{urlparse(settings.host_dashscope).netloc}/api/v1"
)


def bailian_text_img(prompt: str) -> dict:
    """调用文生图模型。

    Returns:
        统一扁平结构,成功与失败字段一致:
        - 成功: {"code": "", "message": "", "url": 图片地址}
        - 失败: {"code": 错误码, "message": 错误信息, "url": ""}
    """
    response = MultiModalConversation.call(
        api_key=settings.dashscope_api_key,
        model="qwen-image-3.0",
        messages=[
            {
                "role": "user",
                "content": [
                    {"text": prompt},
                ],
            }
        ],
        prompt_extend=True,
    )

    if response.status_code != 200:
        log_info(f"文生图调用失败: {response.code} - {response.message}", "temp")
        return {"code": response.code, "message": response.message, "url": ""}

    return {
        "code": "0",
        "message": "接口调用成功",
        "url": _extract_image_url(response),
    }


def _extract_image_url(response) -> str:
    """从文生图响应中提取图片 URL,取不到返回空字符串。"""
    choices = getattr(response.output, "choices", None) or []
    if not choices:
        return ""
    content = choices[0].message.content
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get("image"):
                return item["image"]
    return ""
