from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from database.init_db import get_db
from typing_extensions import Callable, Dict, Any, Awaitable


class DatabaseMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ):
        async for db in get_db():
            data['db'] = db
            resp = await handler(event, data)
            await data['db'].commit()
            return resp