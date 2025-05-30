import abc
from datetime import datetime

from config import settings
from .caching import AbstractCachingService

from openai.types.chat import ChatCompletionMessageParam


class AbstractChatHistoryService(abc.ABC):
    @abc.abstractmethod
    async def add_messages_to_history(self,
                                      user_message: ChatCompletionMessageParam,
                                      assistant_message: ChatCompletionMessageParam,
                                      user_id: int,
                                      chat_type: str,
                                      exp: int = settings.MESSAGES_EXP
                                      ) -> None: ...
    @abc.abstractmethod
    async def add_message_to_history(self, message: ChatCompletionMessageParam,
                                     user_id: int,
                                     chat_type: str,
                                     exp: int = settings.MESSAGES_EXP,
                                     now_ts: float = datetime.utcnow().timestamp()) -> None: ...
    @abc.abstractmethod
    async def get_history(self, user_id: int, chat_type: str) -> list[ChatCompletionMessageParam]: ...

    @abc.abstractmethod
    async def clear_history(self, user_id: int, chat_type: str) -> None: ...


class ChatHistoryService(AbstractChatHistoryService):

    def __init__(self, caching_service: AbstractCachingService):
        self.caching = caching_service
        self.namespace: str = 'history'

    def _create_message_key(self, user_id: int, chat_type: str, timestamp: float) -> str:
        return f'{self.namespace}:{chat_type}:{user_id}:{timestamp}'

    def _create_messages_massive_key(self, user_id: int, chat_type: str) -> str:
        return f'{self.namespace}:{chat_type}:{user_id}'

    async def add_message_to_history(self,
                                     message: ChatCompletionMessageParam,
                                     user_id: int,
                                     chat_type: str,
                                     exp: int = settings.MESSAGES_EXP,
                                     now_ts: float | None = None
                                     ) -> None:
        if not now_ts:
            now_ts = datetime.utcnow().timestamp()
        async with self.caching as cache:
            message_key = self._create_message_key(user_id, chat_type, now_ts)
            await cache.set(message_key, message, exp=exp)
            await cache.zadd(self._create_messages_massive_key(user_id, chat_type), {message_key: now_ts})

    async def get_history(self, user_id: int, chat_type: str, namespace: str = 'history') -> list[ChatCompletionMessageParam]:
        async with self.caching as cache:
            message_keys = await cache.zrange(self._create_messages_massive_key(user_id, chat_type), 0, -1)
            messages = []
            for key in message_keys:
                message = await cache.get(key.decode())
                if message:
                    messages.append(message)
        return messages

    async def add_messages_to_history(self,
                                      user_message: ChatCompletionMessageParam,
                                      assistant_message: ChatCompletionMessageParam,
                                      user_id: int,
                                      chat_type: str,
                                      exp: int = settings.MESSAGES_EXP
                                      ) -> None:
        now_ts = datetime.utcnow().timestamp()
        await self.add_message_to_history(
            user_message, user_id, chat_type, exp, now_ts
        )
        await self.add_message_to_history(
            assistant_message, user_id, chat_type, exp, now_ts+1
        )

    async def clear_history(self, user_id: int, chat_type: str, namespace: str = 'history') -> None:
        async with self.caching as cache:
            message_keys = await cache.zrange(self._create_messages_massive_key(user_id, chat_type), 0, -1)
            await cache.delete(*message_keys)