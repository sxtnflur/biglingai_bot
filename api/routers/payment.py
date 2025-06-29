import datetime
from contextlib import asynccontextmanager

from aiogram import Bot
from bot.keyboards.base import BaseKeyboards
from bot.texts.base import BaseTexts, td_to_text
from config import settings
from depends import logger_service, payment_factory, payments_service, scheduler, subs_service
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


class PaymentAmount(BaseModel):
    value: float
    currency: str


class WebhookObject(BaseModel):
    id: str
    status: str
    metadata: dict = {}
    payment_method: PaymentMethod | None = None
    amount: PaymentAmount


class WebhookPayload(BaseModel):
    event: str
    object: WebhookObject


async def process_pay(
        order_id: str, db: AsyncSession,
        save_payment_method_id: str | None = None,
        payment_method_title: str | None = None
):
    bot = Bot(token=settings.BOT_TOKEN)
    payment = await payments_service.mark_as_paid(
        db=db, bot=bot, order_id=order_id
    )
    text = ''
    if save_payment_method_id:
        await subs_service.add_autopayment_to_user(
            user_id=payment.user.id,
            sub_id=payment.sub.id,
            payment_method_id=save_payment_method_id,
            db=db
        )
        scheduler.autopayment_scheduler.add_job_to_user(payment.user.id, sub_end=payment.user.sub_end)
        text += '✅ Способ оплаты {} сохранен'.format(
            f'<i>{payment_method_title}</i>' if payment_method_title else ''
        )

    if payment.payment.is_auto_paid:
        await bot.send_message(
            chat_id=payment.user.id,
            text='✅ Автооплата прошла успешно!\nВаша подписка продлена и окончится через <code>{}</code>'
            .format(td_to_text(payment.user.td_before_sub_end.days)),
            reply_markup=BaseKeyboards.to_main_menu()
        )
    else:
        await bot.send_message(
            chat_id=payment.user.id,
            text='✅ Оплата прошла успешно!\nВаша подписка окончится через <code>{}</code>'
            .format(td_to_text(payment.user.td_before_sub_end.days)),
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