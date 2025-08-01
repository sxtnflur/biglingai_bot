# grammar_corrector.py
import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from depends import speacker_ai, payment_factory, logger_service, payments_service
from schedulers.autopayment import AutopaymentScheduler


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


# Пример запуска:
if __name__ == "__main__":
    test_autopay()