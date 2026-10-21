"""文件上传:保存上传内容到本地目录,返回相对路径"""

from pathlib import Path

from app.utils import beijing_now

# 与 TTS 落盘目录保持一致,统一放 output/ 下
UPLOAD_DIR = Path("upload")


def save_upload(filename: str, data: bytes) -> str:
    """保存上传的文件内容,返回相对路径(如 output/20261016_..._demo.wav)。

    Args:
        filename: 原始文件名,仅取 basename 防止路径穿越。
        data: 文件内容字节。

    Returns:
        保存后的相对路径。
    """
    UPLOAD_DIR.mkdir(exist_ok=True)
    basename = Path(filename or "file").name  # 去目录部分,防路径穿越
    name = f"{beijing_now().strftime('%Y%m%d_%H%M%S_%f')}_{basename}"
    dest = UPLOAD_DIR / name
    dest.write_bytes(data)
    return str(dest)
