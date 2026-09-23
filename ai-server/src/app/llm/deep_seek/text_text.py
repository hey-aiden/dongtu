from app.config import settings
from langchain_deepseek import ChatDeepSeek

# DeepSeek 偶发把结束符 <|end|> 泄漏到正文(半角/全角多种形态)。
# 显式声明为 stop,让 API 在这些 token 处停止生成,而不是把它们当正文返回。
DEEPSEEK_STOP_TOKENS = [
    "<|end|>",
    "<｜end▁of▁sentence｜>",
    "<|end_of_sentence|>",
    "<|endoftext|>",
]

# llm 应该是进程启动时创建一次就够了，需要的时候import复用；
# 如果通过 depends 调用，等于每个请求新建一个 LLM 客户端——重复创建连接池,浪费且没必要
llm = ChatDeepSeek(
    model=settings.model_deepseek,
    temperature=settings.temperature,
    api_key=settings.api_key_deepseek,
    stop=DEEPSEEK_STOP_TOKENS,
)
