from pydantic.v1 import BaseSettings


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

    START_CREDITS: int = 10
    ADMIN_ID: int = 1304563494

    YOOKASSA_API_KEY: str
    YOOKASSA_SHOP_ID: int


settings = Settings(_env_file='.env')