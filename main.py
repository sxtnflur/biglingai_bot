import asyncio

from aiogram.client.default import DefaultBotProperties
from config import settings
from bot.handlers import __routers__
from aiogram import Bot, Dispatcher

bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
dp = Dispatcher()
dp.include_routers(*__routers__)


async def start_polling():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(start_polling())