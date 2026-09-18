from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .depends import get_instance_db

router = APIRouter()


@router.get("/history_list")
def get_message_list(db: Annotated[AsyncSession, Depends(get_instance_db)]):
    return True


@router.post("/add_msg")
def add_message():
    return False
