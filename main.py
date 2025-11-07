import asyncio
from contextlib import asynccontextmanager

from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand
from aiogram import Bot, Dispatcher, types
from fastapi import FastAPI, Request, BackgroundTasks

from config import settings
from bot.handlers import __routers__
from api.routers import __routers__ as api_routers
from depends import scheduler
import logging

from loader import dp, bot

logging.basicConfig(level=logging.INFO)

dp.include_routers(*__routers__)


async def onstartup(bot: Bot):
    await bot.delete_webhook()
    await bot.set_my_commands(
        commands=[
            BotCommand(
                command='start', description='Перезапустить бота'
            ),
            BotCommand(
                command='support', description='Поддержка'
            )
        ]
    )
    await scheduler.start()


async def start_polling():
    await onstartup(bot)
    await dp.start_polling(bot)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await onstartup(bot)
    await bot.set_webhook(url=settings.BOT_WEBHOOK_URL, request_timeout=60)
    yield
    await bot.delete_webhook()

app = FastAPI(
    root_path=settings.API_PREFIX,
    title="Webhook API", lifespan=lifespan,
    openapi_url=None, docs_url=None, redoc_url=None
)
for router in api_routers:
    app.include_router(router)


async def feed_update(update: types.Update):
    await dp.feed_update(bot=bot, update=update)


@app.post(settings.BOT_WEBHOOK_ENDPOINT)
async def bot_webhook(request: Request, bg_tasks: BackgroundTasks):
    update = types.Update.model_validate(await request.json(), context={"bot": bot})
    bg_tasks.add_task(feed_update, update)

if __name__ == '__main__':
    asyncio.run(start_polling())