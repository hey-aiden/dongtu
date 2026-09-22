"""聊天业务逻辑:滚动摘要、消息构建、agent 调用、落库"""

import re

from app.llm.deep_seek import llm, make_agent
from app.model import ConversationModel, MessageHistoryModel
from app.schemas import MessageRole
from fastapi import HTTPException
from langchain_core.messages import AIMessage, HumanMessage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# 滚动摘要参数
RECENT_KEEP = 10  # 摘要后保留原文的消息条数(窗口大小)
SUMMARY_TRIGGER = 30  # 未摘要的消息超过这个数时,触发滚动摘要

# DeepSeek 偶发把结束符 <|end|> 泄漏到正文。stop 参数已从源头拦截,
# 这里再做一次兜底清理,防止仍有个别变体漏到前端。
_END_TOKEN_RES = [
    re.compile(r"<\|end[^|]*\|>", re.IGNORECASE),  # 半角:<|end|>、<|end_of_sentence|>、<|endoftext|>
    re.compile(r"<｜end[^｜]*｜>"),  # 全角:<｜end▁of▁sentence｜>
]


def _strip_end_tokens(text: str) -> str:
    """去掉可能泄漏的模型结束符"""
    for pattern in _END_TOKEN_RES:
        text = pattern.sub("", text)
    return text.strip()


def _to_langchain_messages(rows: list[MessageHistoryModel]) -> list:
    """把历史消息转成 LangChain 消息列表(只处理 human/ai)"""
    messages = []
    for m in rows:
        if m.role == MessageRole.human.value:
            messages.append(HumanMessage(content=m.msg_content))
        elif m.role == MessageRole.ai.value:
            messages.append(AIMessage(content=m.msg_content))
    return messages


async def _summarize(
    previous_summary: str, old_messages: list[MessageHistoryModel]
) -> str:
    """把最早的旧消息压缩成摘要,合并进已有摘要"""
    text = "\n".join(f"{m.role}: {m.msg_content}" for m in old_messages)
    prompt = (
        "请把下面的对话历史压缩成一段简洁摘要,保留关键信息(用户目标、用户偏好、已确认事项、尚未解决的事情、重要结论);"
        "不要保留： - 寒暄 - 重复解释 - 无关内容 - 已经被后续结论覆盖的信息:\n\n"
        f"已有摘要:\n{previous_summary}\n\n对话内容:\n{text}"
    )
    result = await llm.ainvoke([HumanMessage(content=prompt)])
    return _strip_end_tokens(result.content)


async def send_message(db: AsyncSession, conversation_id: str, content: str) -> dict:
    """发送消息:滚动摘要 + agent 生成回复 + 落库,返回 AI 回复"""
    conv = await db.get(ConversationModel, conversation_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 1. 查历史(时间正序)
    history = (
        await db.scalars(
            select(MessageHistoryModel)
            .where(MessageHistoryModel.conversation_id == conversation_id)
            .order_by(MessageHistoryModel.created_at.asc())
        )
    ).all()

    # 2. 滚动摘要:只压缩「尚未摘要」的消息,避免重复压缩
    summary = conv.summary or ""
    verbatim = history[conv.summarized_count :]  # 标记之后的部分 = 还没被摘要的消息
    if len(verbatim) > SUMMARY_TRIGGER:
        to_summarize = verbatim[
            : len(verbatim) - RECENT_KEEP
        ]  # 只压缩被挤出窗口的最早几条
        summary = await _summarize(summary, to_summarize)
        conv.summary = summary
        conv.summarized_count += len(to_summarize)  # 推进标记

    # 3. 拼消息列表:所有未摘要的原文 + 当前用户输入(避免压缩滞后时丢上下文)
    messages = _to_langchain_messages(history[conv.summarized_count:])
    messages.append(HumanMessage(content=content))

    # 4. 系统提示词(带摘要)
    system_prompt = "你是一个智能助手。"
    if summary:
        system_prompt += f"\n以下是之前对话的摘要:\n{summary}"

    # 5. 调 agent
    agent = make_agent(tools=[], system_prompt=system_prompt)
    result = await agent.ainvoke({"messages": messages})
    ai_content = _strip_end_tokens(result["messages"][-1].content)

    # 6. 落库:用户消息 + AI 回复
    db.add(
        MessageHistoryModel(
            conversation_id=conversation_id,
            role=MessageRole.human.value,
            msg_content=content,
        )
    )
    db.add(
        MessageHistoryModel(
            conversation_id=conversation_id,
            role=MessageRole.ai.value,
            msg_content=ai_content,
        )
    )

    return {"content": ai_content, "role": MessageRole.ai.value}
