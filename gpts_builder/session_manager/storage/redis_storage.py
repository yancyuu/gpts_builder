# -*- coding: utf-8 -*-

import json
from util.base_class.singleton import SingletonMetaThreadSafe
import redis
from util.system import sys_env


class RedisStorage(metaclass=SingletonMetaThreadSafe):

    def __init__(self, url) -> None:
        self._redis = redis.Redis(url=url)

    def set(self, key, data, expired=7200) -> bool:
        if not key:
            raise Exception("找不到key")
        return self._redis.setex(key, expired, json.dumps(data))

    def get(self, key) -> dict:
        if not key:
            raise Exception("找不到key")
        data = self._redis.get(key)
        if not data:
            return {}
        return json.loads(data)

    def check(self, key, expired=24 * 60 * 60) -> bool:
        if not key:
            raise Exception("找不到key")
        return self._redis.expire(key, expired)

    def delete(self, key) -> None:
        if not key:
            raise Exception("找不到key")
        self._redis.delete(key)
    
    def enqueue_message(self, message) -> None:
        """将消息添加到队列中"""
        self._redis.lpush(self.COMMENT_QUEUE_KEY, json.dumps(message))
    
    def dequeue_message(self, timeout=0) -> dict:
        """从队列中移除并返回一条消息"""
        message = self._redis.brpop(self.COMMENT_QUEUE_KEY, timeout=timeout)
        if message:
            return json.loads(message[1])
        return None

    def acquire_lock(self, lock_name, lock_timeout=60):
        """尝试获取锁，成功则返回 True，否则返回 False。"""
        result = self._redis.set(lock_name, 1, ex=lock_timeout, nx=True)
        return result is not None

    def release_lock(self, lock_name):
        """释放锁。"""
        self._redis.delete(lock_name)

