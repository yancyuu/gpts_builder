from ..prompt.builder import PromptBuilder

from ...util.id_generator import generate_common_id


class BaseBuilder(PromptBuilder):

    @staticmethod
    def validate_chat_args(args, model):
        """
        校验传入的参数是否有效，并返回有效的参数。
        :param args: 传入的参数字典
        :return: 过滤后的有效参数字典
        """
        valid_params = {
            'frequency_penalty': lambda x: isinstance(x, (int, float)) and -2.0 <= x <= 2.0,
            'logit_bias': lambda x: isinstance(x, dict) and all(isinstance(k, str) and isinstance(v, (int, float)) and -100 <= v <= 100 for k, v in x.items()),
            'logprobs': lambda x: x in [True, False, None],
            'top_logprobs': lambda x: isinstance(x, int) and 0 <= x <= 20,
            'max_tokens': lambda x: isinstance(x, int) and x > 0,
            'n': lambda x: isinstance(x, int) and x > 0,
            'presence_penalty': lambda x: isinstance(x, (int, float)) and -2.0 <= x <= 2.0,
            'response_format': lambda x: isinstance(x, dict) and x.get("type") == "json_object" and model in ["gpt-4o", "gpt-4-turbo" , "gpt-3.5-turbo"],
            'seed': lambda x: isinstance(x, int) and x >= 0,
            'stop': lambda x: isinstance(x, (str, list)) and (isinstance(x, str) or all(isinstance(i, str) for i in x)),
            'stream_options': lambda x: isinstance(x, dict) or x is None,
            'temperature': lambda x: isinstance(x, (int, float)) and 0 <= x <= 2,
            'top_p': lambda x: isinstance(x, (int, float)) and 0 <= x <= 1,
            'tools': lambda x: isinstance(x, list) and all(isinstance(i, dict) for i in x),
            'tool_choice': lambda x: isinstance(x, (str, dict)) or x is None,
            'user': lambda x: isinstance(x, str)
        }

        validated_args = {}
        for param, validator in valid_params.items():
            if param in args and validator(args[param]):
                validated_args[param] = args[param]
            elif param in args:
                raise ValueError(f"Invalid value for parameter '{param}': {args[param]}")
        
        return validated_args

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


    


    

