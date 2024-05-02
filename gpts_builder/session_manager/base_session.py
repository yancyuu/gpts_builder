from config.config_manager import config_manager

from util.system.sys_env import get_env
from util.logging.logger import logger

import tiktoken
import json


class Session(object):
    """这里主要维护的是大语言模型的上下轮会话"""

    def __init__(self, session_id, system_prompt):
        self.session_id = session_id
        self.messages = []
        self.system_prompt = system_prompt
        
    def to_json(self):
        return json.dumps(self.__dict__)

    @classmethod
    def from_json(cls, json_str, model):
        session_dict = json.loads(json_str)
        session = cls(session_dict['session_id'], system_prompt=session_dict.get('system_prompt', None), model=model)
        session.messages = session_dict.get('messages', [])
        return session

    # 重置会话
    def reset(self):
        system_item = {"role": "system", "content": self.system_prompt}
        self.messages = [system_item]

    def set_system_prompt(self, system_prompt):
        self.system_prompt = system_prompt
        self.reset()

    def add_query(self, query):
        user_item = {"role": "user", "content": query}
        self.messages.append(user_item)

    def add_reply(self, reply):
        assistant_item = {"role": "assistant", "content": reply}
        self.messages.append(assistant_item)

    
    def discard_exceeding(self):
        raise NotImplementedError

    def calc_tokens(self):
        raise NotImplementedError
    
    # refer to https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
    def num_tokens_from_messages(messages, model):
        """Returns the number of tokens used by a list of messages based on dynamically loaded model settings."""
        model_config = config_manager.get_model_config(model)
        
        if not model_config:
            logger.debug(f"Model configuration not found for: {model}")
            return 0

        # Get the token settings for the specified model
        token_setting = config_manager.token_settings.get(model_config['token_setting'], {})
        tokens_per_message = token_setting.get('tokens_per_message', 3)  # Default value if not specified
        tokens_per_name = token_setting.get('tokens_per_name', 1)       # Default value if not specified

        # Get encoding using tiktoken
        try:
            encoding = tiktoken.encoding_for_model(model_config['token_setting'])
        except KeyError:
            logger.debug("Warning: model not found. Using cl100k_base encoding.")
            encoding = tiktoken.get_encoding("cl100k_base")

        num_tokens = 0
        for message in messages:
            num_tokens += tokens_per_message
            for key, value in message.items():
                if key in ['role', 'content']:
                    num_tokens += len(encoding.encode(value))
                if key == "name":
                    num_tokens += tokens_per_name

        num_tokens += 3  # Assuming every reply is primed with "assistant"
        return num_tokens
    
    def num_tokens_by_character(messages):
        """Returns the number of tokens used by a list of messages."""
        tokens = 0
        for msg in messages:
            tokens += len(msg["content"])
        return tokens

