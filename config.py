from pydantic.v1 import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    MESSAGES_EXP: int = 30 * 60
    REDIS_URL: str
    OPENAI_KEY: str
    OPENAI_BASE_URL: str
    OPENAI_MODEL: str

    DATABASE_URL: str

    BOT_TOKEN: str
    BOT_WEBHOOK_URL: str
    BOT_WEBHOOK_ENDPOINT: str

    START_CREDITS: int = 30
    ADMIN_ID: int = 1304563494

    YOOKASSA_API_KEY: str
    YOOKASSA_SHOP_ID: int

    BASE_DIR: str = Path(__file__).resolve(strict=True).parent.__str__()

    ELEVENLABS_API_KEY: str
    ELEVENLABS_MODEL: str
    ELEVENLABS_DEFAULT_VOICE_ID: str


settings = Settings(_env_file='.env')