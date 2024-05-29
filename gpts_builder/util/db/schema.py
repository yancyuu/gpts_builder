ANSWER_TABLE_NAME = "answer"
QUESTION_TABLE_NAME = "question"
KB_TABLE_NAME = "kb"

class EmbbedingSchame:

    def __init__(self, name) -> None:
        self.name = name
        self._id = None
        self._text = None
        self._vector = None
    
    @property
    def id(self):
        if not self._id:
            self._id = f"{self.name}_id"
        return self._id
    
    @property
    def text(self):
        if not self._text:
            self._text = f"{self.name}_text"
        return self._text

    @property
    def vector(self):
        if not self._vector:
            self._vector = f"{self.name}_vector"
        return self._vector
    
    @property
    def kb_id(self):
        return "kb_id"
    
    @property
    def created_at(self):
        return 'create_time'

class DatasetSchema:
    
    @property
    def id(self):
        return 'id'
    
    @property
    def name(self):
        return 'name'
    
    @property
    def creator(self):
        return 'creator'
    
    @property
    def created_at(self):
        return 'create_time'