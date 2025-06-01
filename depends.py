from openai import AsyncOpenAI
from services import (
    CachingService, AbstractCachingService,
    AbstractChatHistoryService, ChatHistoryService,
    LangLearningAIService
)
from config import settings

caching_service: AbstractCachingService = CachingService(redis_url=settings.REDIS_URL)
chat_history_service: AbstractChatHistoryService = ChatHistoryService(caching_service=caching_service)
langlearning_openai_service = LangLearningAIService(
    openai=AsyncOpenAI(
        # api_key='unused',
        # base_url='https://api.llm7.io/v1'
        api_key=settings.OPENAI_KEY, base_url=settings.OPENAI_BASE_URL
    ),
    model=settings.OPENAI_MODEL
)