from ...prompt_base_builder import BaseBuilder
from ...prompt_template import KB_REFERENCE_TEMPLATE
from ...util import logger
from ...session_manager import SessionManagerAsync


class PromptBuilderAsync(BaseBuilder):

    @property
    def session(self):
        return self._session

    def __init__(self, session_id, session_manager: SessionManagerAsync):
            self.session_id = session_id
            self.session_manager = session_manager
            self._session = None
            self._tasks = []
            super().__init__(session_id, session_manager)

    def set_system(self, system_template, **kwargs):
        """设置系统提示词

        Args:
            system_prompt (str): 提示词模板，
            kwargs： 提示词变量渲染参数
        """
        self._tasks.append((self._async_set_system, system_template, kwargs))
        return self

    async def _async_set_system(self, system_template, **kwargs):
        self._set_template(system_template)
        self._render_template(**kwargs)
        logger.info(f"set_system content: {self.content}")
        self._session = await self.session_manager.build_session(self.session_id, self.content)
        logger.info(f"set_system session: {self._session.messages}")

    def set_prompt(self, prompt_template, **kwargs):
        self._tasks.append((self._async_set_prompt, prompt_template, kwargs))
        return self

    async def _async_set_prompt(self, prompt_template, **kwargs):
        self._set_template(prompt_template)
        self._render_template(**kwargs)
        logger.info(f"set_prompt content: {self.content}")
        self._session = await self.session_manager.session_query(self.session_id, self.content)
        logger.info(f"set_prompt session: {self._session.messages}")

    def set_kb_reference(self, **kwargs):
        self._tasks.append((self._async_set_kb_reference, KB_REFERENCE_TEMPLATE, kwargs))
        return self

    async def _async_set_kb_reference(self, kb_reference_template, **kwargs):
        self._set_template(kb_reference_template)
        self._render_template(**kwargs)
        logger.info(f"set_kb_reference content: {self.content}")
        self._session = await self.session_manager.session_query(self.session_id, self.content)
        logger.info(f"set_kb_reference session: {self._session.messages}")

    async def build(self):
        """等待所有异步任务完成"""
        for task, template, kwargs in self._tasks:
            await task(template, **kwargs)
        return self

    

