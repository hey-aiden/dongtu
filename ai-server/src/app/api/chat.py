from uuid import uuid4

from app.db import DbSession
from app.model import ConversationModel, MessageHistoryModel
from app.schemas import (
    ConversationCreate,
    ConversationList,
    ConversationResponse,
    MessageCreate,
    MessageList,
)
from app.services import send_message
from fastapi import APIRouter, Query
from sqlalchemy import func, select

router = APIRouter()


@router.post("/conversation_create", response_model=ConversationResponse)
async def create_conversation(body: ConversationCreate, db: DbSession):
    """创建新会话"""

    conv = ConversationModel(
        conversation_id=uuid4().hex, user_id=body.user_id, title=body.title
    )
    db.add(conv)
    # flush:把 INSERT 发给数据库执行(不提交),让 title/created_at 这类 Python 侧 default 生效
    await db.flush()
    return conv


@router.get("/conversation_list", response_model=ConversationList)
async def get_conversation_list(
    user_id: str,
    db: DbSession,
    page: int = Query(1, ge=1, description="页码,从 1 开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
):
    # page/page_size → offset/limit 换算
    offset = (page - 1) * page_size
    # 单独 count 查询:拿该用户的会话总数(不受分页影响)
    total = await db.scalar(
        select(func.count(ConversationModel.conversation_id)).where(
            ConversationModel.user_id == user_id
        )
    )
    # 列表查询:按创建时间倒序 + 分页
    rows = await db.scalars(
        select(ConversationModel)
        .where(ConversationModel.user_id == user_id)
        .order_by(ConversationModel.created_at.desc())
        .limit(page_size)
        .offset(offset)
    )
    return {"total": total, "items": rows.all()}


@router.post("/message_insert")
async def add_message(body: MessageCreate, db: DbSession):
    """发送消息"""
    return await send_message(db, body.conversation_id, body.content)


@router.get("/message_history_list", response_model=MessageList)
async def get_message_list(
    conversation_id: str,
    db: DbSession,
    page: int = Query(1, ge=1, description="页码,从 1 开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
):
    """查找历史消息记录(分页,最近优先)"""
    offset = (page - 1) * page_size
    # 单独 count 查询:拿该会话的消息总数
    total = await db.scalar(
        select(func.count(MessageHistoryModel.msg_id)).where(
            MessageHistoryModel.conversation_id == conversation_id
        )
    )
    # 列表查询:按时间倒序(最近优先)+ 分页
    rows = (
        await db.scalars(
            select(MessageHistoryModel)
            .where(MessageHistoryModel.conversation_id == conversation_id)
            .order_by(MessageHistoryModel.created_at.desc())
            .limit(page_size)
            .offset(offset)
        )
    ).all()
    items = [
        {"role": m.role, "content": m.msg_content, "created_at": m.created_at}
        for m in rows
    ]
    return {"total": total, "items": items}
