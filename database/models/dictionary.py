from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, IntPk


class DictionaryWord(Base):
    __tablename__ = 'dictionary_words'

    id: Mapped[IntPk]
    word: Mapped[str]
    ru_word: Mapped[str]
    level: Mapped[int]


class UserDictionaryWord(Base):
    __tablename__ = 'users_dictionary_words'

    word_id: Mapped[int] = mapped_column(ForeignKey(DictionaryWord.id), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), primary_key=True)
    learning_rate: Mapped[int] = mapped_column(server_default='0')
    can_be_mark_as_worked: Mapped[bool] = mapped_column(server_default='False')
    is_worked: Mapped[bool] = mapped_column(server_default='False')

    word = relationship(DictionaryWord, foreign_keys=[word_id])