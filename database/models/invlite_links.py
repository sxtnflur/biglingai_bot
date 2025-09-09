from database.models.base import Base, IntPk
from sqlalchemy.orm import Mapped, mapped_column


class InviteLink(Base):
    __tablename__ = 'invite_links'

    key: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]
    sale_percent: Mapped[int]
