from datetime import timedelta, datetime

from database import models
from schedulers import SchedulerServiceProtocol
from schedulers.autopayment import get_job_id
from schemas.subs import CreditsPack, Sub
from services.users_service import UsersService
from sqlalchemy import update, case, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing_extensions import Protocol


class SubsServiceProtocol(Protocol):
    def get_subs(self) -> list[Sub]: ...

    def get_sub(self, id: int) -> Sub: ...

    async def create_or_increase_sub_by_days(
            self, days: int, user_id: int, db: AsyncSession
    ) -> datetime: ...

    async def create_or_increase_sub(
            self, sub_id: int, user_id: int, db: AsyncSession
    ) -> datetime: ...

    async def cancel_autopayment(
            self, user_id: int, db: AsyncSession
    ) -> None: ...


class SubsService(SubsServiceProtocol):
    def __init__(self, scheduler_service: SchedulerServiceProtocol):
        self.scheduler_service = scheduler_service

    def get_credits_packs(self):
        return [
            CreditsPack(
                id=1, credits=50, price=490, sale=None
            ),
            CreditsPack(
                id=2, credits=200, price=990, sale=10
            ),
            CreditsPack(
                id=3, credits=500, price=1490, sale=20
            )
        ]

    def get_credits_pack_by_id(self, id: int):
        return self.get_credits_packs()[id-1]

    def get_subs(self):
        return [
            Sub(
                id=1, name='Турист', days=1, price=49
            ),
            Sub(
                id=2, name='Лингвист', days=30, price=190
            ),
            Sub(
                id=4, name='Носитель', days=90, price=490
            )
        ]

    def get_sub(self, id: int):
        return self.get_subs()[id-1]

    async def create_or_increase_sub_by_days(
        self, days: int, user_id: int, db: AsyncSession
    ) -> datetime:
        return await db.scalar(
            update(models.User)
            .filter(models.User.id == user_id)
            .values(sub_end=case(
                (and_(
                    models.User.sub_end.isnot(None),
                    models.User.sub_end >= func.now()
                ), models.User.sub_end + timedelta(days=days)),
                else_=func.now() + timedelta(days=days)
            ))
            .returning(models.User.sub_end)
        )

    async def create_or_increase_sub(
        self, sub_id: int, user_id: int, db: AsyncSession
    ) -> datetime:
        sub = self.get_sub(sub_id)
        return await self.create_or_increase_sub_by_days(
            days=sub.days, user_id=user_id, db=db
        )

    async def cancel_autopayment(
        self, user_id: int, db: AsyncSession
    ) -> None:
        await db.execute(
            update(models.User)
            .filter(models.User.id == user_id)
            .values(is_autopayment=False)
        )
        self.scheduler_service.autopayment_scheduler.remove_user_job(user_id)

    async def add_autopayment_to_user(self, user_id: int, payment_method_id: str,
                                      autopayment_duration: timedelta,
                                      sub_end: datetime,
                                      db: AsyncSession
                                      ) -> None:
        await UsersService(db).update_user(
            user_tid=user_id,
            payment_method_id=payment_method_id,
            is_autopayment=True,
            autopayment_duration=autopayment_duration
        )
        self.scheduler_service.autopayment_scheduler.add_job_to_user(user_id, sub_end=sub_end)

    # async def return_autopayment_to_user(self, user_id: int, db: AsyncSession):
    #     await UsersService(db).update_user(
    #         user_tid=user_id,
    #         is_autopayment=True
    #     )