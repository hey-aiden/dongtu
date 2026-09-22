from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class MessageRole(str, Enum):
    """消息角色:与 MessageHistoryModel.role 对齐,和 LangChain/LLM 输出一致"""

    human = "human"
    ai = "ai"
    system = "system"
    tool = "tool"


class MessageCreate(BaseModel):
    conversation_id: str
    content: str
    role: MessageRole = MessageRole.human


class MessageResponse(BaseModel):
    """单条消息响应体"""

    role: MessageRole
    content: str
    created_at: datetime


class MessageList(BaseModel):
    """消息历史列表响应体"""

    total: int
    items: list[MessageResponse]
