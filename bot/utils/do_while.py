from typing import Callable

from aiogram import Bot
from typing_extensions import TypeVar, Awaitable, Coroutine
import asyncio


T = TypeVar('T')


async def send_messages_while_do_func(
    coroutine: Awaitable[T], chat_id: int,
    bot: Bot, messages: list[str],
    sleep: float = 1.5
) -> T:
    async def send_typing_action(f_while,
                                 chat_id: int, bot: Bot,
                                 messages: list[str] | None = None,
                                 sleep: float = 1.5):
        message_id = None
        index = 0

        while not f_while():
            try:
                if message_id:
                    await bot.edit_message_text(messages[index], chat_id=chat_id, message_id=message_id)
                else:
                    sent_message = await bot.send_message(chat_id=chat_id, text=messages[index])
                    message_id = sent_message.message_id

                index = (index + 1) % len(messages)

                await asyncio.sleep(sleep)

            except Exception as e:
                print(f"Ошибка при отправке или редактировании сообщения: {e}")
                break

        if message_id:
            await bot.delete_message(chat_id, message_id)

    return await do_while_do(
        coro=coroutine, cycle_func=send_typing_action,
        kwargs=dict(chat_id=chat_id, bot=bot,
                    messages=messages, sleep=sleep)
    )


async def send_action_while_do_func(
        coroutine: Awaitable[T], chat_id: int,
        bot: Bot, action: str,
        sleep: float = 1.5
) -> T:
    async def do(
        f_while: Callable
    ):
        while not f_while():
            try:
                await bot.send_chat_action(
                    chat_id=chat_id, action=action
                )
            except:
                break
            await asyncio.sleep(sleep)
    return await do_while_do(
        coro=coroutine, cycle_func=do
    )


async def do_while_do(
    coro: Awaitable[T],
    cycle_func: Callable[[Callable, ...], Coroutine],
    args: tuple | list | None = None,
    kwargs: dict | None = None
) -> T:
    args = args or []
    kwargs = kwargs or {}

    event = asyncio.Event()
    args.insert(0, event.is_set)

    typing_task = asyncio.create_task(cycle_func(*args, **kwargs))
    try:
        res = await coro
    finally:
        event.set()
        await typing_task
    return res