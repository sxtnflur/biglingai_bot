from contextlib import asynccontextmanager

from aiogram import Bot
from bot.keyboards.base import BaseKeyboards
from bot.texts.base import BaseTexts
from config import settings
from fastapi import APIRouter, Request, Depends
from pydantic import BaseModel
from services.payments_service import PaymentsService
from sqlalchemy.ext.asyncio import AsyncSession
from typing_extensions import Annotated
from database.init_db import async_session, get_db

router = APIRouter()


class WebhookObject(BaseModel):
    id: str
    status: str
    metadata: dict = {}


class WebhookPayload(BaseModel):
    event: str
    object: WebhookObject


async def process_pay(order_id: str, db: AsyncSession):
    bot = Bot(token=settings.BOT_TOKEN)
    payment = await PaymentsService(db).mark_as_paid(
        bot=bot, order_id=order_id
    )
    await bot.send_message(
        chat_id=payment.user.id,
        text='✅ Оплата прошла успешно!\nВаша подписка окончится: {}'
        .format(payment.sub_end.strftime('%H:%M %d.%m.%Y')),
        parse_mode='HTML'
    )
    await bot.send_message(
        chat_id=payment.user.id,
        text=BaseTexts.start(payment.user.first_name, payment.user.credits, payment.sub_end),
        reply_markup=BaseKeyboards.main_menu(),
        parse_mode='HTML'
    )
    await db.commit()


@router.post("/payment/yookassa")
async def yookassa_webhook(
    request: Request, db: Annotated[AsyncSession, Depends(get_db)]
):
    body = await request.body()

    payload = WebhookPayload.parse_raw(body)

    if payload.event != "payment.succeeded":
        return {"status": "ignored"}

    payment_id = payload.object.id

    await process_pay(payment_id, db)
    return {
        'status': 'ok'
    }