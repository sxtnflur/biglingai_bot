from loader import bot
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
from services.ai.elevenlabs_service.lemonfox import LemonfoxService
from services.ai.elevenlabs_service.murf_voice import MurfService
from services.dictionary import DictionaryService
from services.logger import LoggerService
from services.payments_service import PaymentsService
from services.ref_service import RefService
from services.subs_service import SubsService
from services.ai import Elevenlabs

caching_service: AbstractCachingService = CachingService(redis_url=settings.REDIS_URL)

chat_history_service: AbstractChatHistoryService = ChatHistoryService(caching_service=caching_service)

openai_client = AsyncOpenAI(
    api_key=settings.OPENAI_KEY, base_url=settings.OPENAI_BASE_URL
)

# speacker_ai = Elevenlabs(
#     api_key=settings.ELEVENLABS_API_KEY, model=settings.ELEVENLABS_MODEL
# )
# speacker_ai = MurfService(
#     api_key=settings.MURF_API_KEY
# )
speacker_ai = LemonfoxService(
    api_key=settings.LEMONFOX_API_KEY
)

langlearning_openai_service = LangLearningAIService(
    openai=openai_client,
    model=settings.OPENAI_MODEL,
    grammar_ai=GrammarAIService(),
    speacker_ai=speacker_ai
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
который учит английский (от 1 до 100).
Верни несколько вариантов перевода на русский, если слово можно перевести по разному'''
        ).strip()
    )
)

logger_service = LoggerService(
    admin_tg_ids=[
        # -4805765332
    ], bot_token=settings.BOT_TOKEN
)


def get_subs_service():
    return SubsService()


subs_service = get_subs_service()


def get_ref_service():
    return RefService(subs_service=get_subs_service(), bot=bot)


ref_service = get_ref_service()


def get_payments_service():
    return PaymentsService(subs_service=get_subs_service(), ref_service=get_ref_service())


payments_service = get_payments_service()


def get_scheduler():
    return SchedulerService(
        payment_factory=payment_factory,
        logger_service=logger_service,
        payments_service=get_payments_service()
    )


scheduler = get_scheduler()
