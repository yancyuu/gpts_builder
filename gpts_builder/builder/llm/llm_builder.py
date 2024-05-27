from .llm_base_builder import BaseBuilder
from ...config.config_manager import config_manager
from ...session_manager.session_manager import ChatGPTSession
from ...session_manager.session_manager import SessionManager
from ...session_manager.storage.global_storage import global_storage
from ...util.http_client import http_client
from ...util.logger import logger


class LLM(BaseBuilder):

    @property
    def current_plugin(self):
        return self.__current_plugin

    def __init__(self, model, session_storage=None, session_id=None, sessioncls = ChatGPTSession):
        """_summary_

        Args:
            session_id (_type_): 会话ID
            session_storage (_type_, optional): _description_. 会话存储器，默认为None，则为全局变量管理会话，目前还可以配置redis存储.
            sessioncls (_type_, optional): _description_. token管理器，目前只有GPT一种所以可以不传.
        """
        if not config_manager.get_model_config(model):
            raise Exception("没有此模型配置")
        self.session_manager = SessionManager(sessioncls, session_storage if session_storage else global_storage, model)
        super().__init__(session_id=session_id, session_manager=self.session_manager)
        self.__current_plugin = None
    
    @staticmethod
    def embedding(input):
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
        
        logger.info(f"Sending embedding request with payload: {payload} and headers: {headers}")

        response = http_client.post(config_manager.base_url + "/v1/embeddings", json=payload, headers=headers)
        # 记录响应
        logger.info(f"Received embedding response: {response}")

        return response
    
    def chat_completions(self, ** args) -> ChatGPTSession:
        """大模型chat请求
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
        logger.info(f"Sending  chat completions request payload: {payload} headers {headers}")

        response = http_client.post(config_manager.base_url + "/v1/chat/completions", json=payload, headers=headers, timeout=60, max_retries=3)
        # 记录响应
        logger.info(f"Received chat completions response: {response}")

        return response
    

    def chat_completions_stream(self, **args):
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
        return http_client.post_stream(url=url, json=payload, headers=headers, timeout=60)    
    


    

