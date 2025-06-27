from database.models.base import Base, IntPk
from sqlalchemy.orm import Mapped


class Sub(Base):
    __tablename__ = 'subs'

    id: Mapped[IntPk]
    name: Mapped[str]
    days: Mapped[int]
    price: Mapped[int]
    sale: Mapped[int | None]