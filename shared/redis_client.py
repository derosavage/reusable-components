from __future__ import annotations

from typing import Any, Optional

import orjson
from redis.asyncio import ConnectionPool, Redis


class RedisManager:
    def __init__(self, redis_url: str, max_connections: int = 20):
        self.pool = ConnectionPool.from_url(redis_url, max_connections=max_connections)
        self.client = Redis(connection_pool=self.pool)

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        data = orjson.dumps(value)
        await self.client.set(key, data, ex=ttl)

    async def get(self, key: str) -> Any:
        data = await self.client.get(key)
        if data is None:
            return None
        return orjson.loads(data)

    async def delete(self, key: str) -> None:
        await self.client.delete(key)

    async def exists(self, key: str) -> bool:
        return await self.client.exists(key) > 0

    async def expire(self, key: str, ttl: int) -> None:
        await self.client.expire(key, ttl)

    async def hset(self, name: str, key: str, value: Any) -> None:
        data = orjson.dumps(value)
        await self.client.hset(name, key, data)

    async def hget(self, name: str, key: str) -> Any:
        data = await self.client.hget(name, key)
        if data is None:
            return None
        return orjson.loads(data)

    async def hdel(self, name: str, key: str) -> None:
        await self.client.hdel(name, key)

    async def hgetall(self, name: str) -> dict:
        raw = await self.client.hgetall(name)
        return {k.decode(): orjson.loads(v) for k, v in raw.items()}

    async def zadd(self, name: str, mapping: dict) -> None:
        await self.client.zadd(name, mapping)

    async def zremrangebyscore(self, name: str, min_score: float, max_score: float) -> None:
        await self.client.zremrangebyscore(name, min_score, max_score)

    async def zcount(self, name: str, min_score: float, max_score: float) -> int:
        return await self.client.zcount(name, min_score, max_score)

    async def publish(self, channel: str, message: Any) -> None:
        data = orjson.dumps(message)
        await self.client.publish(channel, data)

    async def close(self):
        await self.client.aclose()
        await self.pool.disconnect()
