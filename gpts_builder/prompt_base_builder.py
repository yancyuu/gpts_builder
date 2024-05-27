from .util import logger
from .session_manager.session_manager import SessionManager
import json


class BaseBuilder:

    def __init__(self,  session_id, session_manager: SessionManager, template="Hello, {name}! How can I assist you today?"):
        self.template = template
        self.session_id = session_id
        self.session_manager = session_manager
        self._content = None

    def _set_template(self, new_template):
        """Set a new prompt template."""
        self.template = new_template
        return self
    
    def _render_template(self,  **kwargs):
        """Set a new prompt template."""
        try:
            self.content = self.template.format(**kwargs)
        except KeyError as e:
            logger.info(f"Missing a required key in the template: {e}")
            self._content = self.template  # Return the unmodified template if missing keys
        return self
    
    @staticmethod
    def generate_curl_command(url, json_data, headers):
        """生成curl命令的辅助方法"""
        curl_command = f"curl -X POST '{url}'"
        if headers:
            for key, value in headers.items():
                curl_command += f" -H '{key}: {value}'"
        if json_data:
            json_str = json.dumps(json_data)
            curl_command += f" -d '{json_str}'"
        return curl_command
    


    

