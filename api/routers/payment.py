from fastapi import APIRouter, Request
from pydantic import BaseModel


router = APIRouter()

class WebhookObject(BaseModel):
    id: str
    status: str
    metadata: dict = {}


class WebhookPayload(BaseModel):
    event: str
    object: WebhookObject


@router.post("/webhook/yookassa")
async def yookassa_webhook(
    request: Request,
):
    body = await request.body()

    payload = WebhookPayload.parse_raw(body)

    if payload.event != "payment.succeeded":
        return {"status": "ignored"}

    payment_id = payload.object.id

    # await process_pay(payment_id)
    return {
        'status': 'ok'
    }