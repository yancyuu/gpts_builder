from .llm_base_builder import BaseBuilder
from ...config.config_manager import config_manager
from ...session_manager.session_manager import ChatGPTSession
from ...session_manager.session_manager_async import SessionManagerAsync
from ...session_manager.storage.redis_storage_async import RedisStorageAsync

from ...util.http_client import http_client
from ...util.logger import logger

import json


class LLMAsync(BaseBuilder):

    @property
    def current_plugin(self):
        return self.__current_plugin

    def __init__(self, model, session_storage: RedisStorageAsync, session_id=None, sessioncls = ChatGPTSession):
        """_summary_

        Args:
            session_id (_type_): 会话ID，如果为空，会自动生成一个
            session_storage (_type_, optional): _description_. 会话存储器，异步模式必须配置redis存储.
            sessioncls (_type_, optional): _description_. token管理器，目前只有GPT一种所以可以不传.
        """
        if not config_manager.get_model_config(model):
            raise Exception("没有此模型配置")
        self.session_manager = SessionManagerAsync(sessioncls, session_storage, model)
        super().__init__(session_id=session_id, session_manager=self.session_manager)
        self.__current_plugin = None


    @staticmethod
    async def embedding(input):
        """向OpenAI发送请求，获取文本的embedding"""
        headers = {
            'Authorization': f"Bearer {config_manager.apikey}",
            'Content-Type': 'application/json'
        }
        
        # 准备请求数据
        payload = {
            "input": input,
            "model": "text-embedding-ada-002"
        }
        url = config_manager.base_url + "/v1/embeddings"

        curl_command = BaseBuilder.generate_curl_command(url, payload, headers) 
        logger.info(f"[gpt-builder] {curl_command}")

        response = await http_client.post_async(url=url, json=payload, headers=headers)
        # 记录响应
        logger.info(f"[gpt-builder] Received embedding response: {response}")

        return response
    
    async def chat_completions(self, ** args) -> ChatGPTSession:
        """大模型chat请求，非流式返回
        """
        try:
            # 校验传入的参数
            valid_args = self.validate_chat_args(args, self.session_manager.model)
        except ValueError as e:
            raise Exception(f"Invalid argument: {e}")
        # 1. 准备请求头
        headers = {
            'Authorization': f"Bearer {config_manager.apikey}",
            'Content-Type': 'application/json'
        }
        # 2. 准备请求数据
        payload = {
            "messages": self.session.messages,
            "model": self.session.model
            }
        if args:
            payload.update(valid_args)
        url = config_manager.base_url + "/v1/chat/completions"

        curl_command = BaseBuilder.generate_curl_command(url, payload, headers) 
        logger.info(f"[gpt-builder] {curl_command}")

        return await http_client.post_async(url=url, json=payload, headers=headers, timeout=60, max_retries=3)
    
    async def chat_completions_stream(self, **args):
        """大模型chat请求，流式返回一个异步生成器"""
        try:
            # 校验传入的参数
            valid_args = self.validate_chat_args(args, self.session_manager.model)
        except ValueError as e:
            raise Exception(f"[gpt-builder] Invalid argument: {e}")
        
        # 准备请求头
        headers = {
            'Authorization': f"Bearer {config_manager.apikey}",
            'Content-Type': 'application/json'
        }
        
        # 准备请求数据
        payload = {
            "messages": self.session.messages,
            "model": self.session.model,
            "stream": True
        }
        if args:
            payload.update(valid_args)

        url = config_manager.base_url + "/v1/chat/completions"        
        curl_command = BaseBuilder.generate_curl_command(url, payload, headers) 
        logger.info(f"[gpt-builder] {curl_command}")

        async for line in http_client.post_stream_async(url=url, json=payload, headers=headers, timeout=60):
            yield line 
                        
    


    

