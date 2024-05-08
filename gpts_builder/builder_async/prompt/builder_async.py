from ...prompt_base_builder import BaseBuilder
from ...prompt_template import KB_REFERENCE_TEMPLATE
from ...util import logger
from ...session_manager import SessionManagerAsync

class PromptBuilderAsync(BaseBuilder):

    @property
    def session(self):
        return self._session

    def __init__(self,  session_id, session_manager: SessionManagerAsync):
        self.session_id = session_id
        self.session_manager = session_manager
        self._session = None
    
    async def set_system(self, system_templatet, **kwargs):
        """设置系统提示词

        Args:
            system_prompt (str): 提示词模板，
            kwargs： 提示词变量渲染参数
        """
        self._set_template(system_templatet)
        self._rander_template(**kwargs)
        self._session = await self.session_manager.build_session(self.session_id, self.content)
        return self

    async def set_prompt(self, prompt_template, **kwargs):
        self._set_template(prompt_template)
        self._rander_template(**kwargs)
        self._session = await self.session_manager.session_query(self.session_id, self.content)
        return self

    async def set_kb_reference(self, **kwargs):
        kb_reference_templatet = KB_REFERENCE_TEMPLATE
        self._set_template(kb_reference_templatet)
        self._rander_template(**kwargs)
        self._session = await self.session_manager.session_query(self.session_id, self.content)
        return self


    

