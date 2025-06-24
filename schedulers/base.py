from apscheduler.schedulers.asyncio import AsyncIOScheduler
from typing_extensions import Protocol
from .autopayment import AutopaymentScheduler
from .abc import SchedulerServiceProtocol


class SchedulerService(SchedulerServiceProtocol):
    def __init__(self, payment_factory, logger_service):
        self.scheduler = AsyncIOScheduler()
        self.payment_factory = payment_factory
        self.logger_service = logger_service

    async def start(self) -> None:
        self.scheduler.start()
        await AutopaymentScheduler(
            self.scheduler, self.payment_factory, self.logger_service
        ).restart_autopayment()


