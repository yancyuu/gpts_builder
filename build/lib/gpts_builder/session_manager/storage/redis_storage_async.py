# -*- coding: utf-8 -*-
from ...util.singleton import SingletonMetaThreadSafe
import aioredis
import json


class RedisStorageAsync(metaclass=SingletonMetaThreadSafe):

    def __init__(self, url) -> None:
        self._redis_async = aioredis.from_url(
                url,
                encoding="utf-8",
                decode_responses=True
            )
    
    async def acquire_lock(self, lock_name, lock_timeout=60):
        if lock_timeout == -1:
            # 当不希望键过期时，省略 EX 参数
            result = await self._redis_async.set(lock_name, 1, nx=True)
        else:
            # 确保过期时间是一个正整数
            result = await self._redis_async.set(lock_name, 1, ex=max(1, int(lock_timeout)), nx=True)
        return result is not None


    async def release_lock(self, lock_name):
        """释放锁。"""
        await self._redis_async.delete(lock_name)
    
    async def set(self, key, data, expired=None) -> bool:
        if not key:
            raise Exception("找不到key")
        if expired is None:
            # 没有过期时间，使用set命令
            return await self._redis_async.set(key, json.dumps(data))
        else:
            # 有过期时间，使用setex命令
            return await self._redis_async.setex(key, expired, json.dumps(data))

    async def get(self, key):
        if not key:
            raise Exception("找不到key")
        data = await self._redis_async.get(key)
        return json.loads(data) if data else None

    async def check(self, key, expired=24 * 60 * 60) -> bool:
        if not key:
            raise Exception("找不到key")
        return await self._redis_async.expire(key, expired)

    async def delete(self, key) -> None:
        if not key:
            raise Exception("找不到key")
        await self._redis_async.delete(key)

    async def close(self):
        if self._redis_async:
            self._redis_async.close()
            await self._redis_async.wait_closed()
    
    async def enqueue_message(self, queue_name, message) -> None:
        """异步将消息添加到队列中"""
        await self._redis_async.lpush(queue_name, json.dumps(message))

    async def dequeue_message(self, queue_name, timeout=0) -> dict:
        """异步从队列中移除并返回一条消息"""
        message = await self._redis_async.brpop(queue_name, timeout=timeout)
        if message:
            return json.loads(message[1])
        return None

    async def get_queue_length(self, queue_name):
        """异步获取队列长度"""
        return await self._redis_async.llen(queue_name)
    
