from pydantic import BaseModel
from typing_extensions import Literal
from .ai.openai_base import OpenAIService

LanguageType = Literal['en', 'ru']


class TranslationResult(BaseModel):
    orig: str
    translated: str
    orig_language: LanguageType
    translated_language: LanguageType

    @property
    def en_text(self):
        if self.orig_language == 'en':
            return self.orig
        else:
            return self.translated


class TranslatorService:
    def __init__(self, ai_translator: OpenAIService):
        self.ai_translator = ai_translator

    async def translate(self, text: str, translator: Literal['ai'] = 'ai') -> TranslationResult:
        if translator == 'ai':
            return await self.ai_translator.send_text_get_schema(prompt=text, schema=TranslationResult)