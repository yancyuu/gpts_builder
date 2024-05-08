from ..prompt.builder import PromptBuilder

from ...util.id_generator import generate_common_id


class BaseBuilder(PromptBuilder):

    @property
    def current_plugin(self):
        return self.__current_plugin

    def __init__(self, session_id, session_manager):
        """_summary_

        Args:
            session_id (_type_): 会话ID
            session_storage (_type_, optional): _description_. 会话存储器，默认为None，则为全局变量管理会话，目前还可以配置redis存储.
            sessioncls (_type_, optional): _description_. token管理器，目前只有GPT一种所以可以不传.
        """
        if not session_id:
            session_id = generate_common_id()
        super().__init__(session_id, session_manager)
        self.__current_plugin = None
    
    def set_plugin(self, plugin, **args):
        """动态添加属性到LLM实例。

        Args:
            attr_name (str): 属性名，例如 'kb'
            attr_value (object): 属性值，可以是任何对象，例如 KnowledgeBase 实例
        """
        self.__current_plugin = plugin(**args)


    


    

