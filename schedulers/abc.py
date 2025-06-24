from apscheduler.schedulers.asyncio import AsyncIOScheduler
from typing_extensions import Protocol


class SchedulerServiceProtocol(Protocol):
    scheduler: AsyncIOScheduler
    async def start(self) -> None: ...