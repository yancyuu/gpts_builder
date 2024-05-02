import json
import os
from util.logging.logger import logger
from config import config_template

class ConfigManager:
    def __init__(self, config=None):
        self.config = config if config else config_template
        self.model_settings = []
        self.token_settings = {}
        self.load_config()

    def load_config(self):
        """加载配置文件中的配置到内存。"""
        self.model_settings = self.config.MODEL_SETTINGS
        self.token_settings = self.config.TOKEN_SETTINGS
        self.base_url = self.config.BASE_URL if  self.config.BASE_URL else "https://www.lazygpt.cn/api"
        self.apikey = self.config.API_KEY if self.config.API_KEY else "XXX"


    def get_model_config(self, model_name):
        """根据模型名称获取配置。"""
        for config in self.model_settings:
            if config['model'] == model_name:
                return config
        return None

    def set_model_config(self, model_name, max_tokens, token_setting="gpt-3.5-turbo"):
        """设置或更新模型的最大令牌数，可选更新令牌设置名称。如果模型不存在，则添加新的配置项。"""
        found = False
        for config in self.model_settings:
            if config['model'] == model_name:
                config['max_tokens'] = max_tokens
                if token_setting is not None:
                    config['token_setting'] = token_setting
                found = True
                break
        if not found:
            new_config = {
                "model": model_name, 
                "max_tokens": max_tokens
            }
            if token_setting:
                new_config['token_setting'] = token_setting
            self.model_settings.append(new_config)


config_manager = ConfigManager()