from typing_extensions import Literal
from .ai.openai_base import OpenAIService


class TranslatorService:
    def __init__(self, ai_translator: OpenAIService):
        self.ai_translator = ai_translator

    async def translate(self, text: str, translator: Literal['ai'] = 'ai') -> str:
        if translator == 'ai':
            return await self.ai_translator.send_text_get_text(prompt=text)