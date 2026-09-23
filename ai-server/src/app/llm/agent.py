from langchain.agents import create_agent


#  agent 的正确形态是工厂函数:拿「请求级依赖」进去,返回「这个请求专用」的 agent，而不是进程启动时共享
# *参数表示 后面:tools 和 system_prompt 只能通过关键字传,不能按位置传，eg: build_agent(tools=[...], system_prompt="...")
def make_agent(*, llm, tools, system_prompt):
    """每次请求按需构建 agent,绑定当前请求的工具和提示词"""
    return create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
    )
