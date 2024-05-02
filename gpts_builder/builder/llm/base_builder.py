from builder.prompt.builder import PromptBuilder
from builder.plugin.base_builder import BasePluginBuilder
from config.config_manager import config_manager
from session_manager.chatgpt_session import ChatGPTSession

from util.id_generator import generate_common_id


class BaseBuilder(PromptBuilder):

    @property
    def plugins(self):
        return self.__plugins

    def __init__(self, session_manager, session_id):
        """_summary_

        Args:
            session_id (_type_): 会话ID
            session_storage (_type_, optional): _description_. 会话存储器，默认为None，则为全局变量管理会话，目前还可以配置redis存储.
            sessioncls (_type_, optional): _description_. token管理器，目前只有GPT一种所以可以不传.
        """
        if not session_id:
            session_id = generate_common_id()
        super().__init__(session_id, session_manager)
        self.__plugins = []
    
    def install_plugin(self, plugin):
        """动态添加属性到LLM实例。

        Args:
            attr_name (str): 属性名，例如 'kb'
            attr_value (object): 属性值，可以是任何对象，例如 KnowledgeBase 实例
        """
        plugin_name = plugin.__class__.__name__.lower()
        self.__plugins.append(plugin_name)
        setattr(self, plugin_name, plugin)

    def uninstall_plugin(self, plugin_name):
        if plugin_name in self.__plugins:
            # 移除方法绑定
            delattr(self, plugin_name)
            del self.__plugins[plugin_name]

    


    

