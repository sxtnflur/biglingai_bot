from functools import wraps
from typing import Callable

from sqlalchemy.ext.asyncio import AsyncSession
from .init_db import async_session


def db_connect(kwarg_name: str = 'db', commit: bool = True, rollback: bool = True):
    def bar(func: Callable):
        @wraps(func)
        async def wrapped(*args, **kwargs):
            if kwarg_name in kwargs:
                return await func(*args, **kwargs)

            async with async_session() as sess:
                sess: AsyncSession
                try:
                    result = await func(*args, **{kwarg_name: sess}, **kwargs)
                except Exception as e:
                    if rollback:
                        await sess.rollback()
                    raise e
                else:
                    if commit:
                        await sess.commit()
                return result
        return wrapped
    return bar