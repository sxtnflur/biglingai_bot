from apscheduler.schedulers.asyncio import AsyncIOScheduler
from services.payments_service import PaymentsServiceProtocol
from typing_extensions import Protocol
from .autopayment import AutopaymentScheduler
from .abc import SchedulerServiceProtocol


class SchedulerService(SchedulerServiceProtocol):
    def __init__(self, payment_factory, logger_service, payments_service: PaymentsServiceProtocol):
        self.scheduler = AsyncIOScheduler()
        self.payment_factory = payment_factory
        self.logger_service = logger_service
        self.autopayment_scheduler = AutopaymentScheduler(
            self.scheduler, self.payment_factory, self.logger_service,
            payments_service=payments_service
        )

    async def start(self) -> None:
        self.scheduler.start()
        await self.autopayment_scheduler.restart_autopayment()


