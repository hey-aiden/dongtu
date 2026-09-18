from fastapi import APIRouter

from . import message, user

index_router = APIRouter()

index_router.include_router(user.router, prefix="/user", tags=["user"])
index_router.include_router(message.router, prefix="/messages", tags=["msg"])
