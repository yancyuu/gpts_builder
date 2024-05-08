from .base_session import Session
from ..config.config_manager import config_manager
from ..util.logger import logger


"""
    e.g.  [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Who won the world series in 2020?"},
        {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
        {"role": "user", "content": "Where was it played?"}
    ]
"""


class ChatGPTSession(Session):

    def __init__(self, session_id, system_prompt, model):
        super().__init__(session_id, system_prompt)
        self.model = model
        self.reset()

    def discard_exceeding(self, cur_tokens=None):
        model_config = config_manager.get_model_config(self.model)
        
        if not model_config:
            logger.debug(f"Model configuration not found for: {self.model}")
            return 0

        # Get the token settings for the specified model
        max_tokens = model_config.get('max_tokens', 80000)
        precise = True
        try:
            cur_tokens = self.calc_tokens()
        except Exception as e:
            precise = False
            logger.debug("Exception when counting tokens precisely for query: {}".format(e))
            if cur_tokens is None:
                raise e
        while cur_tokens > max_tokens:
            if len(self.messages) > 2:
                self.messages.pop(1)
            elif len(self.messages) == 2 and self.messages[1]["role"] == "assistant":
                self.messages.pop(1)
                if precise:
                    cur_tokens = self.calc_tokens()
                else:
                    cur_tokens = cur_tokens - max_tokens
                break
            elif len(self.messages) == 2 and self.messages[1]["role"] == "user":
                logger.warning(f"user message exceed max_tokens. total_tokens={cur_tokens}")
                break
            else:
                logger.debug(f"max_tokens={max_tokens}, total_tokens={cur_tokens}, len(messages)={self.messages}")
                break
            if precise:
                cur_tokens = self.calc_tokens()
            else:
                cur_tokens = cur_tokens - max_tokens
        return cur_tokens

    def calc_tokens(self):
        return self.num_tokens_from_messages(self.messages, self.model)


