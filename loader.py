from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis
from config import settings


bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode='HTML',
                                                                 link_preview_is_disabled=True))
storage = RedisStorage(redis=Redis.from_url(settings.REDIS_URL))
dp = Dispatcher()