# grammar_corrector.py
import asyncio

import loader
from api.routers.payment import process_pay
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database.init_db import async_session
from depends import speacker_ai, payment_factory, logger_service, payments_service, langlearning_openai_service, \
    ref_service
from schedulers.autopayment import AutopaymentScheduler
from depends import dictionary_service
from services import GrammarAIService
from services.translator import YandexTranslator


def test_speacker_ai_get_data():
    async def do():
        models = await speacker_ai.get_models()
        voices = await speacker_ai.get_voices()

        print(f'{models=}')
        print(f'{voices=}')
    asyncio.get_event_loop().run_until_complete(do())


def test_autopay():
    autopayment_scheduler = AutopaymentScheduler(
        AsyncIOScheduler(), payment_factory, logger_service,
        payments_service=payments_service
    )

    async def do():
        await autopayment_scheduler.do_pay(user_id=1304563494)
    asyncio.get_event_loop().run_until_complete(do())


async def test_select_trans_word():
    async with async_session() as session:
        orig_words = await dictionary_service.get_user_dictionary_words(
            user_id=6651840737, db=session,

        )
        for word in orig_words:
            print(f'{word=}')
            words = await dictionary_service.get_wrong_words(
                user_id=6651840737,
                exclude_word=word.word.word,
                db=session,
                get_en_words=True
            )
            print(f'{words=}')
            assert word.word.word not in words

            for ru_word in word.word.ru_words:
                words = await dictionary_service.get_wrong_words(
                    user_id=6651840737,
                    exclude_word=ru_word,
                    db=session,
                    get_en_words=False
                )
                assert ru_word not in words


async def translate():
    await YandexTranslator().translate()


async def grammar():
    # res = await GrammarAIService().process_text('today i walked around sochi city and ate very taste food')
    res = await langlearning_openai_service.find_mistakes(
        user_text='hello im fine. what of you?', messages=[]
    )
    print(f'{res=}')


async def get_ref_info():
    async with async_session() as session:
        ref_info = await ref_service.get_user_ref_info(
            db=session,
            user_tid=1304563494,
            bot=loader.bot
        )
        print(f'{ref_info=}')


async def pay():
    async with async_session() as db:
        await process_pay(order_id='31313a5d-000f-5000-8000-1107df57e8e7', db=db)


# Пример запуска:
if __name__ == "__main__":
    asyncio.run(pay())