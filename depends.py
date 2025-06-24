from openai import AsyncOpenAI
from schedulers import SchedulerService
from services import (
    CachingService, AbstractCachingService,
    AbstractChatHistoryService, ChatHistoryService,
    LangLearningAIService, TranslatorService, OpenAIService,
    GrammarAIService
)
from payments import YooKassaService, PaymentFactory
from config import settings
from services.dictionary import DictionaryService
from services.logger import LoggerService
from services.payments_service import PaymentsService
from services.ref_service import RefService
from services.subs_service import SubsService

caching_service: AbstractCachingService = CachingService(redis_url=settings.REDIS_URL)

chat_history_service: AbstractChatHistoryService = ChatHistoryService(caching_service=caching_service)

openai_client = AsyncOpenAI(
    api_key=settings.OPENAI_KEY, base_url=settings.OPENAI_BASE_URL
)

langlearning_openai_service = LangLearningAIService(
    openai=openai_client,
    model=settings.OPENAI_MODEL,
    grammar_ai=GrammarAIService()
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


logger_service = LoggerService(
    admin_tg_ids=[1304563494], bot_token=settings.BOT_TOKEN
)

scheduler = SchedulerService(
    payment_factory=payment_factory,
    logger_service=logger_service
)

subs_service = SubsService(scheduler_service=scheduler)
ref_service = RefService(subs_service=subs_service)
payments_service = PaymentsService(subs_service=subs_service, ref_service=ref_service)