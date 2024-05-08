from ...util.logger import logger

class BasePluginBuilder:
    
    def execute(self, *args, **kwargs):
        """插件执行的具体逻辑"""
        raise NotImplementedError("所有插件必须实现这个方法")


    

