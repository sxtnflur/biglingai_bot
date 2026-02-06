# grammar_corrector.py
import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database.init_db import async_session
from depends import speacker_ai, payment_factory, logger_service, payments_service
from schedulers.autopayment import AutopaymentScheduler
from depends import dictionary_service
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


# Пример запуска:
if __name__ == "__main__":
    asyncio.run(speacker_ai.get_my_voices())