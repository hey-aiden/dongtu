from fastapi import APIRouter

from . import chat, demo, upload, user

index_router = APIRouter()

index_router.include_router(user.router, prefix="/user", tags=["user"])
index_router.include_router(chat.router, prefix="/ai-chat", tags=["msg"])
index_router.include_router(demo.router, prefix="/demo", tags=["demo"])
index_router.include_router(upload.router, prefix="/file", tags=["file"])
