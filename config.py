from pydantic.v1 import BaseSettings


class Settings(BaseSettings):
    MESSAGES_EXP: int = 30 * 60
    REDIS_URL: str
    OPENAI_KEY: str
    OPENAI_BASE_URL: str
    OPENAI_MODEL: str

    DATABASE_URL: str

    BOT_TOKEN: str

    START_CREDITS: int = 10
    ADMIN_ID: int = 1304563494


settings = Settings(_env_file='.env')