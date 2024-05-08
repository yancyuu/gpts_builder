from ...util import logger
from ...session_manager.session_manager import SessionManager

class BaseBuilder:

    def __init__(self,  session_id, session_manager: SessionManager, template="Hello, {name}! How can I assist you today?"):
        self.template = template
        self.session_id = session_id
        self.content = None
        self.session_manager = session_manager

    def _set_template(self, new_template):
        """Set a new prompt template."""
        self.template = new_template
        return self
    
    def _rander_template(self,  **kwargs):
        """Set a new prompt template."""
        try:
            self.content = self.template.format(**kwargs)
        except KeyError as e:
            logger.info(f"Missing a required key in the template: {e}")
            self.content = self.template  # Return the unmodified template if missing keys
        return self
    


    

