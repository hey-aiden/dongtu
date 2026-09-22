from app.config import settings
from langchain.agents import create_agent
from langchain_deepseek import ChatDeepSeek

# llm 应该是进程启动时创建一次就够了，需要的时候import复用；
# 如果通过 depends 调用，等于每个请求新建一个 LLM 客户端——重复创建连接池,浪费且没必要
llm = ChatDeepSeek(
    model=settings.model_deepseek,
    temperature=settings.temperature,
    api_key=settings.api_key_deepseek,
)


#  agent 的正确形态是工厂函数:拿「请求级依赖」进去,返回「这个请求专用」的 agent，而不是进程启动时共享
# *参数表示 后面:tools 和 system_prompt 只能通过关键字传,不能按位置传，eg: build_agent(tools=[...], system_prompt="...")
def make_agent(*, tools, system_prompt):
    """每次请求按需构建 agent,绑定当前请求的工具和提示词"""
    return create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
    )
