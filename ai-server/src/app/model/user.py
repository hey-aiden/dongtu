"""
ORM 模型定义
ForeignKey: 表示当前字段是一个外键
ondelete="CASCADE": 父记录删除时，数据库自动删除关联的子记录
"""

from datetime import datetime, timedelta, timezone

from app.db import Base
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

BEIJING_TZ = timezone(timedelta(hours=8))


def beijing_now() -> datetime:
    """返回北京时间"""
    return datetime.now(BEIJING_TZ).replace(tzinfo=None)


class ConversationModel(Base):
    """
    会话信息表(conversation)
    """

    __tablename__ = "table_chat_conversation"
    conversation_id: Mapped[str] = mapped_column(
        String(64), primary_key=True, comment="会话ID(UUID)"
    )
    user_id: Mapped[str] = mapped_column(
        String(64), index=True, nullable=False, comment="归属用户id"
    )
    title: Mapped[str] = mapped_column(
        String(255), default="新对话", comment="会话标题"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=beijing_now, comment="创建时间"
    )


class MessageHistoryModel(Base):
    """
    聊天历史信息表(chat_message)
    """

    __tablename__ = "table_chat_message"
    msg_id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, comment="自增ID"
    )
    conversation_id: Mapped[str] = mapped_column(
        String(64),
        # ForeignKey 声明引用 table_conversation 表的 conversation_id
        ForeignKey("table_chat_conversation.conversation_id", ondelete="CASCADE"),
        nullable=False,
        comment="外键：会话ID",
    )
    msg_type: Mapped[str] = mapped_column(
        String(32), nullable=False, comment="消息类型：human/ai/system/tool"
    )
    msg_content: Mapped[str] = mapped_column(Text, nullable=False, comment="消息正文")
    create_at: Mapped[datetime] = mapped_column(
        DateTime, default=beijing_now, index=True, comment="消息发送时间"
    )
