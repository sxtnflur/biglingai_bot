from datetime import datetime

from pydantic import BaseModel
from schemas.users import User


class CreditsPack(BaseModel):
    id: int
    credits: int
    price: int
    sale: int | None = None


class Sub(BaseModel):
    id: int
    name: str
    days: int
    price: int
    sale: int | None = None


class Payment(BaseModel):
    id: int
    order_id: str
    amount: int
    created_at: datetime
    paid_at: datetime | None = None

    class Config: from_attributes = True


class SubPaymentResponse(BaseModel):
    sub_end: datetime
    sub: Sub
    payment: Payment
    user: User