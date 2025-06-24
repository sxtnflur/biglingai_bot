import datetime
from contextlib import asynccontextmanager

from aiogram import Bot
from bot.keyboards.base import BaseKeyboards
from bot.texts.base import BaseTexts
from config import settings
from depends import logger_service, payment_factory, payments_service
from fastapi import APIRouter, Request, Depends
from pydantic import BaseModel
from services.payments_service import PaymentsService
from services.users_service import UsersService
from sqlalchemy.ext.asyncio import AsyncSession
from typing_extensions import Annotated
from database.init_db import async_session, get_db

router = APIRouter()


class PaymentMethod(BaseModel):
    id: str
    saved: bool
    title: str


class WebhookObject(BaseModel):
    id: str
    status: str
    metadata: dict = {}
    payment_method: PaymentMethod | None = None


class WebhookPayload(BaseModel):
    event: str
    object: WebhookObject


async def process_pay(
        order_id: str, db: AsyncSession, save_payment_method_id: str | None = None,
        payment_method_title: str | None = None
):
    bot = Bot(token=settings.BOT_TOKEN)
    payment = await payments_service.mark_as_paid(
        db=db, bot=bot, order_id=order_id
    )
    text = ''
    if save_payment_method_id:
        await UsersService(db).update_user(
            user_tid=payment.user.id,
            payment_method_id=save_payment_method_id,
            is_autopayment=True,
            autopayment_duration=datetime.timedelta(days=payment.sub.days)
        )
        text += '✅ Способ оплаты {} сохранен'.format(
            f'<i>{payment_method_title}</i>' if payment_method_title else ''
        )

    await bot.send_message(
        chat_id=payment.user.id,
        text='✅ Оплата прошла успешно!\nВаша подписка окончится: {}'
        .format(payment.sub_end.strftime('%H:%M %d.%m.%Y')),
        parse_mode='HTML'
    )
    await bot.send_message(
        chat_id=payment.user.id,
        text=BaseTexts.start(payment.user.first_name, payment.user.credits, payment.user.td_before_sub_end),
        reply_markup=BaseKeyboards.main_menu(),
        parse_mode='HTML'
    )
    await db.commit()
    await logger_service.log_by_telegram_bot(
        f'Пользователь: {payment.user.full_name} @{payment.user.username} {payment.user.id}\n'
        f'Купил подписку {payment.sub.name} ({payment.sub.days} дней) на сумму: {payment.payment.amount} руб\n'
        f'Подписка кончится: {payment.sub_end}'
    )


@router.post("/payment/yookassa")
async def yookassa_webhook(
    request: Request, db: Annotated[AsyncSession, Depends(get_db)]
):
    body = await request.body()

    try:
        payload: WebhookPayload = WebhookPayload.parse_raw(body)

        if payload.event != "payment.succeeded":
            return {"status": "ignored"}

        print(f'{payload.object=}')

        await process_pay(
            payload.object.id, db,
            save_payment_method_id=payload.object.payment_method.id if payload.object.payment_method.saved else None,
            payment_method_title=payload.object.payment_method.title if payload.object.payment_method.saved else None
        )
        return {
            'status': 'ok'
        }
    except Exception as e:
        await logger_service.log_by_telegram_bot(
            f'Оплата не прошла!\n\n'
            f'Тело запроса: {body}\n\n'
            f'Ошибка: {e}'
        )