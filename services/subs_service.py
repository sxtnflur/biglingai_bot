from datetime import timedelta, datetime

from database import models
from schedulers import SchedulerServiceProtocol
from schemas.subs import CreditsPack, Sub
from services.users_service import UsersService
from sqlalchemy import update, case, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing_extensions import Protocol


class SubsServiceProtocol(Protocol):
    async def get_subs(self, db: AsyncSession) -> list[Sub]: ...

    async def get_sub(self, id: int, db: AsyncSession) -> Sub: ...

    async def create_or_increase_sub_by_days(
            self, sub_id: int, days: int, user_id: int, db: AsyncSession
    ) -> datetime: ...

    async def create_or_increase_sub(
            self, sub_id: int, user_id: int, db: AsyncSession
    ) -> datetime: ...

    async def cancel_autopayment(
            self, user_id: int, db: AsyncSession
    ) -> None: ...


class SubsService(SubsServiceProtocol):

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

    async def get_subs(self, db: AsyncSession) -> list[Sub]:
        subs = await db.scalars(
            select(models.Sub)
            .order_by(models.Sub.price.asc())
        )
        return list(map(Sub.model_validate, subs))

    async def get_sub(self, id: int, db: AsyncSession) -> Sub | None:
        return await db.scalar(
            select(models.Sub)
            .filter(models.Sub.id == id)
        )

    # def get_subs_by_filters(self, **filters) -> list[Sub]:
    #     def f(x: Sub):
    #         for k, v in filters.items():
    #             return getattr(x, k, None) == v
    #
    #     return filter(f, self.get_subs())

    def get_sub_by_filters(self, **filters) -> Sub | None:
        res = self.get_subs_by_filters(**filters)
        if res:
            return res[0]

    async def create_or_increase_sub_by_days(
        self, sub_id: int, days: int, user_id: int, db: AsyncSession
    ) -> datetime:
        # TODO: изменить minutes -> days
        td = timedelta(days=days)
        return await db.scalar(
            update(models.User)
            .filter(models.User.id == user_id)
            .values(sub_end=case(
                (and_(
                    models.User.sub_end.isnot(None),
                    models.User.sub_end >= func.now()
                ), models.User.sub_end + td),
                else_=func.date_trunc('minute', func.now()) + td
            ),
                current_sub_id=sub_id)
            .returning(models.User.sub_end)
        )

    # async def create_or_increase_sub(
    #     self, sub_id: int, user_id: int, db: AsyncSession
    # ) -> datetime:
    #     sub = self.get_sub(sub_id)
    #     return await self.create_or_increase_sub_by_days(
    #         days=sub.days, user_id=user_id, db=db
    #     )

    async def cancel_autopayment(
        self, user_id: int, db: AsyncSession
    ) -> None:
        await db.execute(
            update(models.User)
            .filter(models.User.id == user_id)
            .values(is_autopayment=False, payment_method_id=None)
        )

    async def add_autopayment_to_user(self,
                                      user_id: int,
                                      payment_method_id: str,
                                      sub_id: int,
                                      db: AsyncSession
                                      ) -> None:
        await UsersService(db).update_user(
            user_tid=user_id,
            current_sub_id=sub_id,
            payment_method_id=payment_method_id,
            is_autopayment=True
        )
