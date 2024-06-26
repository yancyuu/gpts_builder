from ...prompt_base_builder import BaseBuilder
from ...prompt_template import KB_REFERENCE_TEMPLATE
from ...util.logger import logger
from ...session_manager import SessionManager

class PromptBuilder(BaseBuilder):

    @property
    def session(self):
        return self._session


    def __init__(self, session_id, session_manager: SessionManager):
        self.template = None
        self._session = None
        self.session_id = session_id
        self.session_manager = session_manager
        self._tasks = []
        self._content = None

    def set_system(self, system_template, **kwargs):
        """设置系统提示词

        Args:
            system_prompt (str): 提示词模板，
            kwargs： 提示词变量渲染参数
        """
        self._tasks.append(lambda: self._sync_set_system(system_template, **kwargs))
        return self

    def _sync_set_system(self, system_template, **kwargs):
        self._set_template(system_template)
        self._render_template(**kwargs)
        self._content = self.content
        self._session = self.session_manager.build_session(self.session_id, self._content)
        logger.info(f"set_system res {self._session.messages}")

    def set_prompt(self, prompt_template, **kwargs):
        self._tasks.append(lambda: self._sync_set_prompt(prompt_template, **kwargs))
        return self

    def _sync_set_prompt(self, prompt_template, **kwargs):
        self._set_template(prompt_template)
        self._render_template(**kwargs)
        self._content = self.content
        self._session = self.session_manager.session_query(self.session_id, self._content)
        logger.info(f"set_prompt res {self._session.messages}")

    def set_kb_reference(self, **kwargs):
        self._tasks.append(lambda: self._sync_set_kb_reference(**kwargs))
        return self

    def _sync_set_kb_reference(self, **kwargs):
        kb_reference_template = KB_REFERENCE_TEMPLATE
        self._set_template(kb_reference_template)
        self._render_template(**kwargs)
        self._content = self.content
        self._session = self.session_manager.session_query(self.session_id, self._content)
        logger.info(f"set_kb_reference res {self._session.messages}")

    def build(self):
        """执行所有任务"""
        for task in self._tasks:
            task()
        return self


    

