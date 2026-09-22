from pydantic import BaseModel, ConfigDict


class ConversationCreate(BaseModel):
    """创建会话请求体"""

    user_id: str
    title: str = "新对话"


class ConversationResponse(BaseModel):
    """会话响应体"""

    model_config = ConfigDict(from_attributes=True)

    conversation_id: str
    user_id: str
    title: str


class ConversationList(BaseModel):
    total: int
    items: list[ConversationResponse]
