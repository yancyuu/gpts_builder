from ..util.logger import logger
from .config_template import MODEL_SETTINGS, TOKEN_SETTINGS, BASE_URL, API_KEY
import json


class ConfigManager:
    
    def __init__(self, config_file=None):
        """
        __init__ 初始化配置管理器。

        Args:
            config_file: 配置文件路径。如果不提供，则使用默认配置。
        """
        self.model_settings = []
        self.token_settings = {}
        self.load_config(config_file)   

    def load_config(self, config_file=None):
        """加载配置文件中的配置到内存。"""
        if config_file:
            # 从文件中加载配置
            with open(config_file, 'r') as f:
                config = json.load(f)
            self.model_settings = config.get('MODEL_SETTINGS', MODEL_SETTINGS)
            self.token_settings = config.get('TOKEN_SETTINGS', TOKEN_SETTINGS)
            self.base_url = config.get('BASE_URL', BASE_URL if BASE_URL else "https://www.lazygpt.cn/api")
            self.apikey = config.get('API_KEY', API_KEY if API_KEY else "XXX")
        else:
            # 使用默认配置
            self.model_settings = MODEL_SETTINGS
            self.token_settings = TOKEN_SETTINGS
            self.base_url = BASE_URL if BASE_URL else "https://www.lazygpt.cn/api"
            self.apikey = API_KEY if API_KEY else "XXX"


    def get_model_config(self, model_name):
        """根据模型名称获取配置。"""
        for config in self.model_settings:
            if config['model'] == model_name:
                return config
        return None
    
    def list_models_config(self):
        """将类中的属性转换为JSON输出。"""
        # 获取所有实例属性
        config_dict = {key: value for key, value in self.__dict__.items() if not key.startswith('_')}
        return json.dumps(config_dict, indent=4)

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