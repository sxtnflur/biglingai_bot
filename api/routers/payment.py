from contextlib import asynccontextmanager

from aiogram import Bot
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
    await PaymentsService(db).mark_as_paid(
        bot=Bot(token=settings.BOT_TOKEN), order_id=order_id
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