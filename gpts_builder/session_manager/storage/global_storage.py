"""用户进程内部通讯的的公共变量"""
from ...util.singleton import SingletonMetaThreadSafe as SingletonMetaclass
from ...util.logger import logger
import json

"""
    e.g.  [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Who won the world series in 2020?"},
        {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
        {"role": "user", "content": "Where was it played?"}
    ]
"""


class GlobalStorage(metaclass=SingletonMetaclass):
    """
    如果没有传入redis客户端，则用全局变量管理会话
    """

    def __init__(self):
        self.global_map = {}
    
    def set(self, key, data, expired=24 * 60 * 60) -> bool:
        if not key:
            raise Exception("找不到key")
        self.global_map[key] = json.dumps(data)
    
    def get(self, key) -> dict:
        if not key:
            raise Exception("找不到key")
        data = self.global_map.get(key)
        return json.loads(data) if data else None
    
    def delete(self, key) -> bool:
        if not key:
            raise Exception("找不到key")
        if key in self.global_map:
            del self.global_map[key]
        return True



global_storage = GlobalStorage()