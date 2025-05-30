from datetime import datetime
from enum import Enum, auto

from database.models.base import Base, IntPk, CreatedAt
from sqlalchemy import BIGINT
from sqlalchemy.orm import Mapped, mapped_column


class PaymentType(Enum):
    sub = auto()
    credits = auto()


class Payment(Base):
    __tablename__ = 'payments'

    id: Mapped[IntPk]
    order_id: Mapped[str | None]
    user_id: Mapped[int] = mapped_column(BIGINT)
    amount: Mapped[int]
    type: Mapped[PaymentType]
    created_at: Mapped[CreatedAt]
    paid_at: Mapped[datetime | None]
    test: Mapped[bool]