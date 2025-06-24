from uuid import UUID

from sqlalchemy import TEXT, BIGINT, ARRAY, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, IntPk, CreatedAt


class MistakeType(Base):
    __tablename__ = 'mistake_types'

    key: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]


class Mistake(Base):
    __tablename__ = 'mistakes'

    id: Mapped[IntPk]
    user_id: Mapped[int] = mapped_column(BIGINT)
    type_key: Mapped[str] = mapped_column(ForeignKey(MistakeType.key))
    # group: Mapped[str]
    # subgroup: Mapped[str]
    incorrect: Mapped[str]
    correct: Mapped[str]
    example: Mapped[list[str]] = mapped_column(ARRAY(String))
    explanation: Mapped[str] = mapped_column(TEXT)
    dialog_uuid: Mapped[UUID]
    user_message: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    is_worked_out: Mapped[bool] = mapped_column(server_default='False')
    date: Mapped[CreatedAt]

    type = relationship(MistakeType, foreign_keys=[type_key])