from fastapi import APIRouter

from . import chat, demo, user

index_router = APIRouter()

index_router.include_router(user.router, prefix="/user", tags=["user"])
index_router.include_router(chat.router, prefix="/ai-chat", tags=["msg"])
index_router.include_router(demo.router, prefix="/demo", tags=["demo"])
