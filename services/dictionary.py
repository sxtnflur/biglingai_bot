from config import settings
from database import models
from openai import AsyncOpenAI
from schemas.dictionary import DictionaryWord, AIGeneratedDictionaryWord, DictionaryWordWithUserInfo, UserWord, \
    UserDictionaryWord
from services import OpenAIService
from sqlalchemy import select, insert, func, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing_extensions import Literal


class DictionaryService:
    def __init__(self, openai_service: OpenAIService):
        self.__openai = openai_service

    async def join_dictionary_word_to_user(
            self, word_id: int, user_id: int, db: AsyncSession
    ):
        await db.execute(
            insert(models.UserDictionaryWord)
            .values(
                user_id=user_id, word_id=word_id
            )
        )

    async def add_word_to_dictionary(
            self, word: str, ru_word: str, level: int, db: AsyncSession
    ) -> int:
        return await db.scalar(
            insert(models.DictionaryWord)
            .values(word=word, ru_word=ru_word, level=level)
            .returning(models.DictionaryWord.id)
        )

    async def join_or_generate_word(
            self, word: str, user_id: int, db: AsyncSession
    ) -> DictionaryWord:
        existed_word: models.DictionaryWord | None = await db.scalar(
            select(models.DictionaryWord)
            .filter(models.DictionaryWord.word == word)
        )
        if existed_word:
            word_id = existed_word.id
            await self.join_dictionary_word_to_user(word_id, user_id, db=db)
            result_word = DictionaryWord.model_validate(existed_word)
        else:
            ai_resp = await self.__openai.send_text_get_schema(
                prompt=word,
                schema=AIGeneratedDictionaryWord
            )
            word_id = await self.add_word_to_dictionary(
                word=ai_resp.word.word.capitalize(),
                ru_word=ai_resp.word.ru_word.capitalize(),
                level=ai_resp.word.level,
                db=db
            )
            await self.join_dictionary_word_to_user(word_id, user_id, db=db)
            result_word = DictionaryWord.model_validate(
                ai_resp.word.model_dump() | {'id': word_id}
            )
        return result_word

    async def get_random_user_word_from_dictionary(
        self, user_id: int, db: AsyncSession, exclude_words: list[str] | None = None
    ) -> DictionaryWordWithUserInfo | None:
        stmt = (
            select(models.DictionaryWord, models.UserDictionaryWord)
            .join(models.UserDictionaryWord, models.UserDictionaryWord.word_id == models.DictionaryWord.id)
            .filter(
                models.UserDictionaryWord.user_id == user_id,
                models.UserDictionaryWord.is_worked.is_not(True)
            )
            .order_by(func.random())
            .limit(1)
        )
        if exclude_words:
            stmt = stmt.filter(models.DictionaryWord.word.notin_(exclude_words))

        res = await db.execute(stmt)
        if not res:
            return
        word, user_info = res.fetchone()
        if not word or not user_info:
            return
        print(f'{word.__dict__=}')
        print(f'{user_info.__dict__=}')
        return DictionaryWordWithUserInfo(
            word=DictionaryWord.model_validate(word),
            user_info=UserWord.model_validate(user_info)
        )

    async def get_random_word_from_dictionary(
        self, db: AsyncSession, user_id: int, user_level: int = 1,
        exclude_words: list[str] | None = None
    ) -> DictionaryWord:
        '''
        Возвращает случайное слово ближайшее по уровню к указанному и не изученное пользователем

        :param db:
        :param exclude_words:
        :param user_id: ID юзера
        :param user_level: Уровень юзера
        :return:
        '''
        # Подзапрос: id всех слов, где is_worked = True у этого пользователя
        subq_worked_words = (
            select(models.UserDictionaryWord.word_id)
            .where(
                models.UserDictionaryWord.user_id == user_id,
                models.UserDictionaryWord.is_worked == True
            )
        ).subquery()

        # Слова, подходящие по уровню и не отмеченные как is_worked
        stmt = (
            select(DictionaryWord)
            .where(
                ~models.DictionaryWord.id.in_(subq_worked_words)
            )
            .order_by(func.abs(DictionaryWord.level - user_level))  # ближайший уровень
            .limit(1)  # ограничим для случайного выбора
        )
        if exclude_words:
            stmt = stmt.filter(models.DictionaryWord.word.notin_(exclude_words))
        word = await db.scalar(stmt)
        return DictionaryWord.model_validate(word)

    async def change_word_learning_rate(
            self, db: AsyncSession,
            word_id: int, user_id: int,
            change_for_amount: int,
            increase: bool = True
    ) -> int:
        stmt = (
            update(models.UserDictionaryWord)
            .filter(
                models.UserDictionaryWord.word_id == word_id,
                models.UserDictionaryWord.user_id == user_id
            )
        )
        if increase:
            stmt = stmt.values(learning_rate=models.UserDictionaryWord.learning_rate + change_for_amount)
        else:
            stmt = stmt.values(learning_rate=models.UserDictionaryWord.learning_rate - change_for_amount)
        stmt = stmt.returning(models.UserDictionaryWord.learning_rate)
        return await db.scalar(stmt)

    async def mark_word_as_can_be_mark_as_worked(
            self, word_id: int, user_id: int, db: AsyncSession
    ) -> None:
        await db.execute(
            update(models.UserDictionaryWord)
            .filter(models.UserDictionaryWord.user_id == user_id,
                    models.UserDictionaryWord.word_id == word_id)
            .values(can_be_mark_as_worked=True)
        )

    async def mark_word_as_worked(
            self, word_id: int, user_id: int, db: AsyncSession
    ) -> None:
        await db.execute(
            update(models.UserDictionaryWord)
            .filter(
                models.UserDictionaryWord.user_id == user_id,
                models.UserDictionaryWord.word_id == word_id
            )
            .values(is_worked=True)
        )

    async def count_user_dictionary_words(
        self, user_id: int, db: AsyncSession
    ) -> int:
        return await db.scalar(
            select(func.count())
            .select_from(models.UserDictionaryWord)
            .filter(models.UserDictionaryWord.user_id == user_id)
        )

    async def get_user_dictionary_words(
        self, user_id: int, db: AsyncSession,
        offset: int = 0, limit: int = 10,
        order_by: Literal['alphabet'] = 'alphabet',
        order_asc: bool = True
    ) -> list[UserDictionaryWord]:
        print(f'{order_by=}')
        stmt = (
            select(models.UserDictionaryWord)
            .options(
                selectinload(models.UserDictionaryWord.word)
            )
            .join(models.UserDictionaryWord.word)
            .filter(
                models.UserDictionaryWord.user_id == user_id,

            )
        )
        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)
        if order_by:
            order_by_field = None
            if order_by == 'alphabet':
                order_by_field = models.DictionaryWord.word
            elif order_by == 'learning_rate':
                order_by_field = models.UserDictionaryWord.learning_rate

            if order_by_field:
                if order_asc:
                    stmt = stmt.order_by(order_by_field.asc())
                else:
                    stmt = stmt.order_by(order_by_field.desc())

        objs = await db.scalars(stmt)
        return list(map(UserDictionaryWord.model_validate, objs))