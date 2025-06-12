from openai import AsyncOpenAI
from services import (
    CachingService, AbstractCachingService,
    AbstractChatHistoryService, ChatHistoryService,
    LangLearningAIService, TranslatorService, OpenAIService
)
from payments import YooKassaService, PaymentFactory
from config import settings
from services.dictionary import DictionaryService

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
        system_message=(
            "You are a translator from English to Russian and from Russian to English. "
            "Only translate the messages that are being sent to you and don't do anything else"
        )
    )
)

dictionary_service = DictionaryService(
    openai_service=OpenAIService(
        openai_client=openai_client,
        model='openai/gpt-4.1-mini',
        system_message=(
'''
Если отправленное тебе пользователем слово не на английском, верни {word: null, is_en_word: False}.
Если слово на английском, переведи слово и укажи его уровень сложности для человека, 
который учит английский (от 1 до 100)'''
        )
    )
)