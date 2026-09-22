"""
ORM 模型定义
ForeignKey: 表示当前字段是一个外键
ondelete="CASCADE": 父记录删除时，数据库自动删除关联的子记录
"""

from datetime import datetime

from app.db import Base
from app.utils import beijing_now
from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column


class MessageHistoryModel(Base):
    """
    聊天历史信息表(chat_message)
    """

    __tablename__ = "table_chat_message"
    # __table_args__:表级配置(复合索引、联合唯一约束等),单列索引用 mapped_column(index=True)
    __table_args__ = (
        Index("idx_conv_created", "conversation_id", "created_at"),  # 复合索引:覆盖「按会话查 + 按时间排序」
    )

    msg_id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, comment="自增ID"
    )
    conversation_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("table_chat_conversation.conversation_id", ondelete="CASCADE"),
        nullable=False,
        comment="外键：会话ID",
    )
    role: Mapped[str] = mapped_column(
        String(32), nullable=False, comment="消息角色：human/ai/system/tool"
    )
    msg_content: Mapped[str] = mapped_column(Text, nullable=False, comment="消息正文")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=beijing_now, comment="消息发送时间"
    )
