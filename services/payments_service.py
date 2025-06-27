from datetime import timedelta

from aiogram import Bot
from database import models
from schemas.subs import SubPaymentResponse, Payment
from services.ref_service import RefService
from services.subs_service import SubsServiceProtocol
from sqlalchemy import insert, update, func, case, and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing_extensions import Protocol


class PaymentsServiceProtocol(Protocol):
    async def save_payment(
            self,
            db: AsyncSession,
            user_tid: int,
            amount: int,
            sub_id: int,
            order_id: str | None = None,
            test: bool = True
    ) -> None: ...

    async def save_autopayment(
            self,
            db: AsyncSession,
            user_tid: int,
            amount: int,
            sub_id: int,
            order_id: str
    ) -> None: ...
    async def mark_as_paid(
            self, db: AsyncSession, order_id: str, bot: Bot
    ) -> SubPaymentResponse: ...


class PaymentsService(PaymentsServiceProtocol):
    def __init__(
            self,
            subs_service: SubsServiceProtocol,
            ref_service: RefService
    ):
        self.subs_service = subs_service
        self.ref_service = ref_service

    async def save_payment(
        self,
        db: AsyncSession,
        user_tid: int,
        amount: int,
        sub_id: int,
        order_id: str | None = None,
        test: bool = True
    ) -> None:
        await db.execute(
            insert(models.Payment)
            .values(
                user_id=user_tid, amount=amount,
                test=test, order_id=order_id,
                sub_id=sub_id
            )
        )

    async def save_autopayment(
        self,
        db: AsyncSession,
        user_tid: int,
        amount: int,
        sub_id: int,
        order_id: str
    ) -> None:
        await db.execute(
            insert(models.Payment)
            .values(
                user_id=user_tid, amount=amount,
                order_id=order_id,
                sub_id=sub_id, paid_at=func.now(),
                is_auto_paid=True
            )
        )

    async def mark_as_paid(
        self, db: AsyncSession, order_id: str, bot: Bot
    ) -> SubPaymentResponse:
        payment: models.Payment | None = await db.scalar(
            update(models.Payment)
            .filter(models.Payment.order_id == order_id)
            .values(paid_at=func.now())
            .returning(models.Payment)
        )
        if not payment:
            raise Exception('Платеж "{}" не найден'.format(order_id))

        sub = await self.subs_service.get_sub(payment.sub_id, db=db)
        sub_end = await self.subs_service.create_or_increase_sub_by_days(
            days=sub.days, user_id=payment.user_id, db=db
        )
        user = await db.scalar(
            select(models.User).filter(models.User.id == payment.user_id)
        )
        await self.ref_service.on_user_paid(
            db=db, user_tid=payment.user_id, amount=payment.amount, sub_id=payment.sub_id, bot=bot
        )
        return SubPaymentResponse(
            sub_end=sub_end,
            payment=Payment.model_validate(payment),
            user=user,
            sub=sub
        )