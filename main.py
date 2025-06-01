import asyncio

from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand
from config import settings
from bot.handlers import __routers__
from aiogram import Bot, Dispatcher

bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
dp = Dispatcher()
dp.include_routers(*__routers__)


async def onstartup(bot: Bot):
    await bot.set_my_commands(
        commands=[
            BotCommand(
                command='start', description='Перезапустить бота'
            )
        ]
    )


async def start_polling():
    await onstartup(bot)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(start_polling())