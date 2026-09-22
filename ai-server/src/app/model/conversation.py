from datetime import datetime

from app.db import Base
from app.utils import beijing_now
from sqlalchemy import DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column


class ConversationModel(Base):
    """
    会话信息表(conversation)
    """

    __tablename__ = "table_chat_conversation"
    # __table_args__:表级配置(复合索引、联合唯一约束等),单列索引用 mapped_column(index=True)
    __table_args__ = (
        Index("idx_user_created", "user_id", "created_at"),  # 复合索引:覆盖「按用户查 + 按时间排序」
    )

    conversation_id: Mapped[str] = mapped_column(
        String(64), primary_key=True, comment="会话ID(UUID)"
    )
    user_id: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="归属用户id"
    )
    title: Mapped[str] = mapped_column(
        String(255), default="新对话", comment="会话标题"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=beijing_now, comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=beijing_now, onupdate=beijing_now, comment="最后活跃时间"
    )
    summary: Mapped[str | None] = mapped_column(
        Text, nullable=True, default=None, comment="历史对话滚动摘要"
    )
    summarized_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="已压缩进摘要的消息条数(摘要覆盖到前几条)"
    )
