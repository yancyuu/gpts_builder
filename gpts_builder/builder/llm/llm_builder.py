from builder.llm.base_builder import BaseBuilder
from config.config_manager import config_manager
from session_manager.chatgpt_session import ChatGPTSession
from session_manager.session_manager import SessionManager
from session_manager.session_manager_async import SessionManagerAsync
from session_manager.storage.global_storage import global_storage
from util.http_client import http_client
from util.logging.logger import logger
from util.id_generator import generate_common_id


class LLM(BaseBuilder):

    def __init__(self, model, session_storage=None, session_id=None, sessioncls = ChatGPTSession):
        """_summary_

        Args:
            session_id (_type_): 会话ID
            session_storage (_type_, optional): _description_. 会话存储器，默认为None，则为全局变量管理会话，目前还可以配置redis存储.
            sessioncls (_type_, optional): _description_. token管理器，目前只有GPT一种所以可以不传.
        """
        if not config_manager.get_model_config(model):
            raise Exception("没有此模型配置")
        session_manager = SessionManager(sessioncls, session_storage if session_storage else global_storage, model)
        super().__init__(session_id=session_id, session_manager=session_manager)
    
    def chat_completions(self):
        """大模型chat请求
        """
        headers = {
            'Authorization': f"Bearer {config_manager.apikey}",
            'Content-Type': 'application/json'
        }
        plody = {
            "messages": self.session.messages,
            "model": self.session.model
            }
        logger.info(f"chat_completions  post {plody} headers {headers}")

        reply = http_client.post(config_manager.base_url + "/v1/chat/completions", json=plody, headers=headers, timeout=60, max_retries=3)
        logger.info(f"chat_completions res {reply}")
        content = reply.get("choices")[0].get("message",{}).get("content") if reply.get("choices") else ""
        session = self.session_manager.session_reply(self.session.session_id, content)
        logger.info(f"session_reply res {session.messages}")
        return reply
    

class LLMAsync(BaseBuilder):

    def __init__(self, model, session_storage, session_id=None, sessioncls = ChatGPTSession):
        """_summary_

        Args:
            session_id (_type_): 会话ID，如果为空，会自动生成一个
            session_storage (_type_, optional): _description_. 会话存储器，异步模式必须配置redis存储.
            sessioncls (_type_, optional): _description_. token管理器，目前只有GPT一种所以可以不传.
        """
        if not config_manager.get_model_config(model):
            raise Exception("没有此模型配置")
        session_manager = SessionManagerAsync(sessioncls, session_storage, model)
        super().__init__(session_id=session_id, session_manager=session_manager)

    
    async def chat_completions(self):
        """大模型chat请求
        """
        headers = {
            'Authorization': f"Bearer {config_manager.apikey}",
            'Content-Type': 'application/json'
        }
        plody = {
            "messages": self.session.messages,
            "model": self.session.model
            }
        logger.info(f"chat_completions  post {plody} headers {headers}")
        reply = await http_client.post(config_manager.base_url + "/v1/chat/completions", json=plody, headers=headers, timeout=60, max_retries=3)
        content = reply.get("choices")[0].get("message",{}).get("content") if reply.get("choices") else ""
        session = self.session_manager.session_reply(self.session.session_id, content)
        logger.info(f"session_reply res {session.messages}")
        return reply
    


    

