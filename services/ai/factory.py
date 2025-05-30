from openai import AsyncOpenAI
from services.ai.openai_base import OpenAIService


class AIFactory:

    def get_openai(self, system_prompt: str | None = None, default_model: str | None = None) -> OpenAIService:
        return OpenAIService(
            openai_client=AsyncOpenAI()
        )