from aiogram import Bot
from database import models
from services.ref_service import RefService
from sqlalchemy import insert, update, func
from sqlalchemy.ext.asyncio import AsyncSession


class PaymentsService:
    def __init__(self, db: AsyncSession):
        self.__db = db

    async def save_payment(
        self,
        user_tid: int,
        amount: int,
        type: models.PaymentType,
        order_id: str | None = None,
        test: bool = True
    ) -> None:
        await self.__db.execute(
            insert(models.Payment)
            .values(
                user_id=user_tid, amount=amount,
                type=type, test=test, order_id=order_id
            )
        )

    async def mark_as_paid(
        self, order_id: str, bot: Bot
    ) -> models.Payment:
        payment: models.Payment | None = await self.__db.scalar(
            update(models.Payment)
            .filter(models.Payment.order_id == order_id)
            .values(paid_at=func.now())
            .returning(models.Payment)
        )
        if not payment:
            raise Exception('Платеж "{}" не найден'.format(order_id))
        await RefService(self.__db).on_user_paid(payment.user_id, payment.amount, bot=bot)
        return payment