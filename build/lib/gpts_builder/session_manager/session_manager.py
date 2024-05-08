# chatGPT的session管理器,用来存放进程中的一些全局变量，比如上下文回话
from ..util.logger import logger
from .chatgpt_session import ChatGPTSession

from .storage.global_storage import GlobalStorage
from .storage.redis_storage import RedisStorage
from typing import Type, Optional


class SessionManager(object):
    """这里主要是更新真实的上下文缓存"""

    def __init__(self, sessioncls: Type[ChatGPTSession], session_storage: RedisStorage | GlobalStorage, model):
        self.session_storage = session_storage
        self.sessioncls = sessioncls
        self.expires_in_seconds = 3600
        self.model = model

    def build_session(self, session_id, system_prompt=None):
        if session_id is None:
            return self.sessioncls(session_id)
        
        session_json = self.session_storage.get(session_id)

        if session_json is None:
            session = self.sessioncls(session_id, system_prompt, self.model)
            self.session_storage.set(session_id, session.to_json())
        else:
            
            session = self.sessioncls.from_json(session_json, self.model)
            if system_prompt is not None:
                self.sessioncls.set_system_prompt(system_prompt)
            self.session_storage.set(session_id, session.to_json(), self.expires_in_seconds)
        
        return session

    def session_query(self, session_id, query):
        session = self.build_session(session_id)
        session.add_query(query)
        self.session_storage.set(session_id, session.to_json(), self.expires_in_seconds)
        try:
            total_tokens = session.discard_exceeding()
            logger.debug("prompt tokens used={}".format(total_tokens))
        except Exception as e:
            logger.debug("Exception when counting tokens precisely for prompt: {}".format(str(e)))
        return session

    def session_reply(self, session_id, reply, total_tokens=None):
        session = self.build_session(session_id)
        session.add_reply(reply)
        self.session_storage.set(session_id, session.to_json(), self.expires_in_seconds)    
        try:
            tokens_cnt = session.discard_exceeding(total_tokens)
            logger.debug("raw total_tokens={}, savesession tokens={}".format(total_tokens, tokens_cnt))
        except Exception as e:
            logger.debug("Exception when counting tokens precisely for session: {}".format(str(e)))
        return session

    def clear_session(self, session_id):
        self.session_storage.delete(session_id)
