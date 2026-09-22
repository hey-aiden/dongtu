"""
Depends 依赖注入数据库会话的使用示例

核心契约(get_db 在 app/db/core.py):
  1. 成功     -> 请求返回后自动 commit
  2. 抛异常   -> 自动 rollback 并重新抛出
  3. 无论成败 -> 最后 close

因此接口里:
  - 写操作:只需 db.add() + flush/refresh,不用手动 commit
  - 读操作:用 SQLAlchemy 2.0 的 select() 查询
"""

from uuid import uuid4

from app.db import DbSession
from app.model import ConversationModel, MessageHistoryModel
from app.schemas import ConversationCreate, ConversationResponse, MessageCreate
from fastapi import APIRouter
from sqlalchemy import select

router = APIRouter()


# ---------- 写:新增会话 ----------


@router.post("/conversation", response_model=ConversationResponse)
async def create_conversation(body: ConversationCreate, db: DbSession):
    """POST /demo/conversation  演示写操作"""
    conv = ConversationModel(
        conversation_id=uuid4().hex,
        user_id=body.user_id,
        title=body.title,
    )
    db.add(conv)
    await db.flush()  # 触发 INSERT,让 default 字段(title/created_at)生效
    await db.refresh(conv)  # 回读数据库,拿到默认值
    # 注意:这里不手动 commit,get_db 会在响应返回后统一 commit
    return conv


# ---------- 读:查询会话列表 ----------


@router.get("/conversations/{user_id}", response_model=list[ConversationResponse])
async def list_conversations(user_id: str, db: DbSession):
    """GET /demo/conversations/{user_id}  演示读操作"""
    result = await db.scalars(
        select(ConversationModel)
        .where(ConversationModel.user_id == user_id)
        .order_by(ConversationModel.created_at.desc())
    )
    return result.all()


# ---------- 写:新增消息(第二个表) ----------


@router.post("/message")
async def add_message(body: MessageCreate, db: DbSession):
    """POST /demo/message  演示往第二个表写数据"""
    msg = MessageHistoryModel(
        conversation_id=body.conversation_id,
        role=body.role,
        msg_content=body.content,  # app.schemas.MessageCreate 的字段是 content,对应 ORM 的 msg_content
    )
    db.add(msg)
    await db.flush()  # flush 后自增 ID msg_id 已可用
    return {"msg_id": msg.msg_id, "status": "ok"}
