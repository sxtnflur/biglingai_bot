from datetime import datetime
from uuid import UUID

from sqlalchemy import BIGINT
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, CreatedAt, UpdatedAt


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    username: Mapped[str | None]
    first_name: Mapped[str]
    last_name: Mapped[str | None]
    credits: Mapped[int] = mapped_column(server_default='0')
    sub_end: Mapped[datetime | None]

    invited_by_id: Mapped[int | None] = mapped_column(BIGINT, nullable=True)
    credits_from_refs: Mapped[int] = mapped_column(server_default='0')

    paid_refs_percent: Mapped[int | None]
    paid_refs_balance: Mapped[int | None]

    special_ref_on_moderation: Mapped[bool] = mapped_column(server_default='False')

    created_at: Mapped[CreatedAt]
    updated_at: Mapped[UpdatedAt]