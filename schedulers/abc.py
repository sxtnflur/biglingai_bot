from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from typing_extensions import Protocol


class SchedulerServiceProtocol(Protocol):
    scheduler: AsyncIOScheduler
    autopayment_scheduler: 'AutopaymentSchedulerProtocol'
    async def start(self) -> None: ...


class AutopaymentSchedulerProtocol(Protocol):
    async def do_pay(self, user_id: int): ...

    def remove_user_job(self, user_id: int) -> None: ...

    def add_job_to_user(self, user_id: int, sub_end: datetime): ...

    async def restart_autopayment(self): ...