from openai import AsyncOpenAI
from services import (
    CachingService, AbstractCachingService,
    AbstractChatHistoryService, ChatHistoryService,
    LangLearningAIService, TranslatorService, OpenAIService
)
from payments import YooKassaService, PaymentFactory
from config import settings

caching_service: AbstractCachingService = CachingService(redis_url=settings.REDIS_URL)

chat_history_service: AbstractChatHistoryService = ChatHistoryService(caching_service=caching_service)

openai_client = AsyncOpenAI(
    api_key=settings.OPENAI_KEY, base_url=settings.OPENAI_BASE_URL
)

langlearning_openai_service = LangLearningAIService(
    openai=openai_client,
    model=settings.OPENAI_MODEL
)

payment_factory = PaymentFactory(yookassa=YooKassaService(
    shop_id=settings.YOOKASSA_SHOP_ID,
    api_token=settings.YOOKASSA_API_KEY
))

translator = TranslatorService(
    ai_translator=OpenAIService(
        openai_client=openai_client,
        model='openai/gpt-4.1-mini',
        system_message='Ты переводчик с англйского на русский или с русского на английский. '
                       'Переводи сообщения, которые тебе отправляют'
    )
)