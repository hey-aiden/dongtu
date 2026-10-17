from typing import Annotated

from app.services import save_upload
from fastapi import APIRouter, File, UploadFile

router = APIRouter()


@router.post("/upload_file")
async def upload_file(file: Annotated[UploadFile, File(...)]):
    """上传文件:保存到本地目录,返回相对路径。"""
    data = await file.read()
    path = save_upload(file.filename, data)
    return {"file_path": path}
