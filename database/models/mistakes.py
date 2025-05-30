from uuid import UUID

from sqlalchemy import TEXT, BIGINT, ARRAY, String
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, IntPk, CreatedAt


class Mistake(Base):
    __tablename__ = 'mistakes'

    id: Mapped[IntPk]
    user_id: Mapped[int] = mapped_column(BIGINT)
    group: Mapped[str]
    subgroup: Mapped[str]
    incorrect: Mapped[str]
    correct: Mapped[str]
    example: Mapped[list[str]] = mapped_column(ARRAY(String))
    explanation: Mapped[str] = mapped_column(TEXT)
    dialog_uuid: Mapped[UUID]
    user_message: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    date: Mapped[CreatedAt]