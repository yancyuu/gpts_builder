from gpts_builder.builder import LLM
from gpts_builder.builder_async import LLMAsync
from gpts_builder.session_manager.storage.redis_storage_async import RedisStorageAsync

from gpts_builder.config import config_manager

from gpts_builder.util.logger import logger

import asyncio

"""
大预言模型的demo
"""

# 查看所有模型的配置
configs = config_manager.list_models_config()
print(configs)
config_manager.base_url = "https://www.lazygpt.cn/api"
config_manager.apikey = "lazygpt-MHXlP7AniCHUsgzm0ylyz2vcvxp6j"


async def llm_async_demo():
    """
    llm_async_demo 测试异步LLM的demo
    """
    ### example0: 初始化LLM（开启一轮对话）
    # 异步的session存储需要设置，目前只支持redis存储
    session_storage = RedisStorageAsync("redis://localhost:6379")
    llm = LLMAsync(model="gpt-3.5-turbo", session_storage=session_storage)
    # 设置系统提示词和用户输入
    await llm.set_system("你是一个AI助理").set_prompt("测试回复").build()

    ### example1: 测试一轮对话，返回所有结果
    # 获取非流式回复
    reply = await llm.chat_completions()
    print(f"Received reply {reply}")
    content = reply.get("choices")[0].get("message",{}).get("content") if reply.get("choices") else ""
    print(f"Received content {content}")

    ### example2: 测试一轮对话，流式返回所有结果（获取流式回复：流式返回为一个异步生成器，需要迭代生成）
    async for content in llm.chat_completions_stream():
        print(f"Received content: {content}")
    
    ### example3: 查看当前会话的历史消息
    session = llm.session
    print(f"Session messages: {session.to_json()}")


def llm_sync_demo():
    """
    llm_sync_demo 测试同步LLM的demo
    """
    ### example0: 初始化LLM（开启一轮对话）
    # session存储支持redis存储｜全局变量存储，如果不传session_storage则默认使用全局变量存储
    llm = LLM(model="gpt-3.5-turbo")
    llm.set_system("这里填系统提示词").set_prompt("这里填提示词模板和参数或者内容").build()

    ### example1: 测试一轮对话，返回所有结果
    replay = llm.chat_completions()
    content = replay.get("choices")[0].get("message",{}).get("content") if replay.get("choices") else ""
    print(f"Received content: {content}")

    ### example2: 测试一轮对话，流式返回所有结果（流式返回为一个异步生成器，需要迭代生成）
    for content in llm.chat_completions_stream():
        print(f"Received content: {content}")

    ### example3: 查看当前会话的历史消息
    session = llm.session
    print(f"Session messages: {session.to_json()}")
    

if __name__ == "__main__":
    asyncio.run(llm_async_demo())
    # llm_sync_demo()


    
