from datetime import timedelta

from aiogram import Bot
from database import models
from schemas.subs import SubPaymentResponse, Payment
from services.ref_service import RefService
from services.subs_service import SubsService
from sqlalchemy import insert, update, func, case, and_, select
from sqlalchemy.ext.asyncio import AsyncSession


class PaymentsService:
    def __init__(self, db: AsyncSession):
        self.__db = db

    async def save_payment(
        self,
        user_tid: int,
        amount: int,
        sub_id: int,
        order_id: str | None = None,
        test: bool = True
    ) -> None:
        await self.__db.execute(
            insert(models.Payment)
            .values(
                user_id=user_tid, amount=amount,
                test=test, order_id=order_id,
                sub_id=sub_id
            )
        )

    async def mark_as_paid(
        self, order_id: str, bot: Bot
    ) -> SubPaymentResponse:
        payment: models.Payment | None = await self.__db.scalar(
            update(models.Payment)
            .filter(models.Payment.order_id == order_id)
            .values(paid_at=func.now())
            .returning(models.Payment)
        )
        if not payment:
            raise Exception('Платеж "{}" не найден'.format(order_id))

        sub = SubsService().get_sub(payment.sub_id)
        sub_end = await self.__db.scalar(
            update(models.User)
            .filter(models.User.id == payment.user_id)
            .values(sub_end=case(
                (and_(
                    models.User.sub_end.isnot(None),
                    models.User.sub_end >= func.now()
                ), models.User.sub_end + timedelta(days=sub.days))
            ))
            .returning(models.User.sub_end)
        )
        user = await self.__db.scalar(
            select(models.User).filter(models.User.id == payment.user_id)
        )
        await RefService(self.__db).on_user_paid(payment.user_id, payment.amount, bot=bot)
        return SubPaymentResponse(
            sub_end=sub_end,
            sub=sub,
            payment=Payment.model_validate(payment),
            user=user
        )