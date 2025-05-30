import abc

# import aioredis
# from aioredis.client import AnyKeyT, KeyT
# from aioredis.connection import EncodableT
from redis.asyncio import Redis
from redis.typing import KeyT, AnyKeyT, EncodableT
from typing_extensions import Mapping
from pickle import dumps, loads


class AbstractCachingService(abc.ABC):
    @abc.abstractmethod
    async def connect(self):
        ...

    @abc.abstractmethod
    async def disconnect(self):
        ...

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

    @abc.abstractmethod
    async def set(self, name: str, value, exp: int):
        ...

    @abc.abstractmethod
    async def zadd(self, name: KeyT, mapping: Mapping[AnyKeyT, EncodableT]):
        ...

    @abc.abstractmethod
    async def get(self, name: str):
        ...
    @abc.abstractmethod
    async def zrange(self, name: str, start: int, end: int):
        ...
    @abc.abstractmethod
    async def delete(self, *names: str) -> None:
        ...
    @abc.abstractmethod
    async def delete_keys_startswith(self, startswith: str):
        ...


class CachingService(AbstractCachingService):
    def __init__(self, redis_url: str):
        self.url = redis_url

    async def connect(self):
        self._client = Redis.from_url(self.url)

    async def disconnect(self):
        pass
        # await self.client.close()

    async def set(self, name: str, value, exp: int):
        value = dumps(value)
        await self._client.set(name, value, exp)

    async def zadd(self, name: KeyT, mapping: Mapping[AnyKeyT, EncodableT]):
        await self._client.zadd(name, mapping)

    async def get(self, name: str):
        val = await self._client.get(name)
        if not val:
            return val
        return loads(val)

    async def zrange(self, name: str, start: int, end: int):
        res = await self._client.zrange(name, start, end)
        return res

    async def delete(self, *names: str) -> None:
        await self._client.delete(*names)

    async def delete_keys_startswith(self, startswith: str):
        keys = await self._client.keys(match=startswith)
        await self.delete(*keys)