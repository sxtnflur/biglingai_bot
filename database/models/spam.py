from datetime import datetime

from enums import Audience
from sqlalchemy import JSON, ARRAY, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from database.models.base import Base, IntPk, CreatedAt


class SpamMessage(Base):
    __tablename__ = 'spam_messages'
    __table_args__ = {'schema': 'spam'}

    id: Mapped[IntPk]
    text: Mapped[str | None]
    media: Mapped[dict | None] = mapped_column(JSON)
    keyboard: Mapped[list[list[dict]] | None] = mapped_column(JSONB)
    audience: Mapped[Audience] = mapped_column(Enum(Audience, schema='spam'), default=Audience.all, server_default=str(Audience.all))

    sent_at: Mapped[datetime | None]
