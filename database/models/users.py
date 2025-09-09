from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import BIGINT, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, CreatedAt, UpdatedAt


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    username: Mapped[str | None]
    first_name: Mapped[str]
    last_name: Mapped[str | None]
    credits: Mapped[int] = mapped_column(server_default='0')
    sub_end: Mapped[datetime | None]
    current_sub_id: Mapped[int | None] = mapped_column(ForeignKey('subs.id'))

    payment_method_id: Mapped[str | None]
    is_autopayment: Mapped[bool] = mapped_column(server_default='False')
    # autopayment_duration: Mapped[timedelta | None]

    invited_by_id: Mapped[int | None] = mapped_column(BIGINT, nullable=True)
    credits_from_refs: Mapped[int] = mapped_column(server_default='0')

    paid_refs_percent: Mapped[int | None]
    paid_refs_balance: Mapped[int | None]

    special_ref_on_moderation: Mapped[bool] = mapped_column(server_default='False')

    sale_percent: Mapped[int | None]

    created_at: Mapped[CreatedAt]
    updated_at: Mapped[UpdatedAt]

    current_sub = relationship('Sub', foreign_keys=[current_sub_id])