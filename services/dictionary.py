from config import settings
from database import models
import random
from openai import AsyncOpenAI
from schemas.dictionary import DictionaryWord, AIGeneratedDictionaryWord, DictionaryWordWithUserInfo, UserWord, \
    UserDictionaryWord
from services import OpenAIService
from sqlalchemy import select, insert, func, update, and_, text, desc
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
            text('''
            INSERT INTO users_dictionary_words (user_id, word_id)
            VALUES (:user_id, :word_id)
            ON CONFLICT (user_id, word_id) DO NOTHING
            ''').bindparams(user_id=user_id, word_id=word_id)
        )

    async def add_word_to_dictionary(
            self, word: str, ru_words: list[str], level: int, db: AsyncSession
    ) -> int:
        return await db.scalar(
            insert(models.DictionaryWord)
            .values(word=word, ru_words=ru_words, level=level)
            .returning(models.DictionaryWord.id)
        )

    async def get_randow_word_to_train(self, user_id: int, db: AsyncSession, last_word: str | None = None):
        count_available_words = await self.count_user_dict_words(
            user_id=user_id, db=db,
            can_be_mark_as_worked=False, is_worked=False
            # only_cant_be_worked=True, only_not_worked=True
        )
        print(f'{count_available_words=}')

        # Если слов меньше 10, берем слово из чужого словаря с элементом рандома
        if (count_available_words <= 1) or (count_available_words < 10 and random.randint(0, 2)):
            user_level = await self.count_user_level(
                user_id=user_id, db=db
            )
            word = await self.get_random_word_from_dictionary(
                db=db,
                user_id=user_id,
                user_level=user_level,
                exclude_words=[last_word],
                exclude_all_user_words=True
            )
            await self.join_dictionary_word_to_user(
                word_id=word.id, user_id=user_id, db=db
            )
            learning_rate = 0
        else:
            word_data = await self.get_random_user_word_from_dictionary(
                user_id=user_id, db=db, exclude_words=[last_word]
            )
            word = word_data.word
            learning_rate = word_data.user_info.learning_rate
        return word, learning_rate

    async def join_or_generate_word(
            self, word: str, user_id: int, db: AsyncSession
    ) -> DictionaryWord:
        existed_word: models.DictionaryWord | None = await db.scalar(
            select(models.DictionaryWord)
            .filter(models.DictionaryWord.word.ilike(word.lower()))
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
                ru_words=list(map(lambda x: x.capitalize(), ai_resp.word.ru_words)),
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
        res = res.fetchone()
        if not res:
            return
        word, user_info = res
        if not word or not user_info:
            return
        print(f'{word.__dict__=}')
        print(f'{user_info.__dict__=}')
        return DictionaryWordWithUserInfo(
            word=DictionaryWord.model_validate(word),
            user_info=UserWord.model_validate(user_info)
        )

    async def get_random_word_from_dictionary(
        self, db: AsyncSession, user_id: int, user_level: float = 1,
        exclude_all_user_words: bool = False,
        exclude_words: list[str] | None = None
    ) -> DictionaryWord:
        """
        Возвращает случайное слово ближайшее по уровню к указанному и не изученное пользователем

        :param exclude_all_user_words:
        :param db:
        :param exclude_words:
        :param user_id: ID юзера
        :param user_level: Уровень юзера
        :return:
        """
        # Подзапрос: id всех слов, где is_worked = True у этого пользователя
        subq_worked_words = (
            select(models.UserDictionaryWord.word_id)
            .where(
                models.UserDictionaryWord.user_id == user_id
            )
        )
        if not exclude_all_user_words:
            subq_worked_words = subq_worked_words.filter(
                models.UserDictionaryWord.is_worked.is_(True)
            )

        # Слова, подходящие по уровню и не отмеченные как is_worked
        stmt = (
            select(models.DictionaryWord)
            .where(
                ~models.DictionaryWord.id.in_(subq_worked_words.subquery())
            )
            .order_by(func.abs(models.DictionaryWord.level - user_level),
                      func.random()
                      )  # ближайший уровень
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

    async def mark_word_as_already_know(self, word: str, user_id: int, db: AsyncSession):
        await db.execute(
            update(models.UserDictionaryWord)
            .filter(
                models.UserDictionaryWord.user_id == user_id,
                models.UserDictionaryWord.word_id == (
                    select(models.DictionaryWord.id).filter(models.DictionaryWord.word == word)
                ).subquery()
            )
            .values(already_know=True, is_worked=True, can_be_mark_as_worked=True)
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
        return await self.count_user_dict_words(
            user_id=user_id, db=db
            # only_not_worked=False, only_cant_be_worked=False
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

    async def count_user_dict_words(
            self, user_id: int, db: AsyncSession,
            is_worked: bool = None,
            can_be_mark_as_worked: bool = None,
            already_know: bool = None

            # only_not_worked: bool = True,
            # only_cant_be_worked: bool = True,
            # only_already_know: bool = False,
            # only_not_already_know: bool = False
    ) -> int:
        stmt = (
            select(func.count())
            .filter(
                models.UserDictionaryWord.user_id == user_id
            )
        )
        if is_worked is not None:
            stmt = stmt.filter(models.UserDictionaryWord.is_worked.is_(is_worked))
        if can_be_mark_as_worked is not None:
            stmt = stmt.filter(models.UserDictionaryWord.can_be_mark_as_worked.is_(can_be_mark_as_worked))
        if already_know is not None:
            stmt = stmt.filter(models.UserDictionaryWord.already_know.is_(already_know))
        return await db.scalar(stmt)

    async def count_user_level(self, user_id: int, db: AsyncSession) -> float:
        stmt = (
            select(func.avg(models.DictionaryWord.level))
            .select_from(models.UserDictionaryWord)
            .filter(
                models.UserDictionaryWord.word_id == models.DictionaryWord.id,
                models.UserDictionaryWord.user_id == user_id,
                models.UserDictionaryWord.can_be_mark_as_worked.is_(True)
            )
        )
        return await db.scalar(stmt) or 0

    async def get_wrong_words(
            self,
            user_id: int,
            exclude_word: str,  # Всегда английское слово
            db: AsyncSession,
            count_words: int = 5,
            get_en_words: bool = True
    ) -> list[str]:

        # Находим все русские переводы исключаемого английского слова
        exclude_translations_stmt = (
            select(models.DictionaryWord.ru_words)
            .where(models.DictionaryWord.word == exclude_word)
        )
        exclude_translations_result = await db.scalars(exclude_translations_stmt)
        exclude_translations_lists = exclude_translations_result.all()

        # Разворачиваем список списков в плоский список
        exclude_translations = []
        for translation_list in exclude_translations_lists:
            if translation_list:
                exclude_translations.extend(translation_list)

        if get_en_words:
            # Возвращаем английские слова
            word_field = models.DictionaryWord.word

            # Исключаем слова с общими переводами
            from sqlalchemy import or_

            if exclude_translations:
                # Создаем условия для каждого исключаемого перевода
                exclude_conditions = or_(*[
                    models.DictionaryWord.ru_words.any(translation)
                    for translation in exclude_translations
                ])

                words_with_common_translations = (
                    select(models.DictionaryWord.id)
                    .where(exclude_conditions)
                ).scalar_subquery()
            else:
                words_with_common_translations = select(None).where(False).scalar_subquery()

            stmt = (
                select(word_field)
                .select_from(models.UserDictionaryWord)
                .join(models.UserDictionaryWord.word)
                .filter(
                    models.UserDictionaryWord.user_id == user_id,
                    models.DictionaryWord.word != exclude_word,
                    ~models.DictionaryWord.id.in_(words_with_common_translations)
                )
                .limit(count_words)
                .order_by(func.random())
            )
        else:
            # Возвращаем русские слова, исключая переводы исключаемого слова
            # Сначала находим все ID слов пользователя
            user_words_subq = (
                select(models.DictionaryWord.id)
                .select_from(models.UserDictionaryWord)
                .join(models.UserDictionaryWord.word)
                .filter(models.UserDictionaryWord.user_id == user_id)
                .subquery()
            )

            # Затем разворачиваем русские слова и фильтруем их
            stmt = (
                select(func.unnest(models.DictionaryWord.ru_words).label("random_ru_word"))
                .where(
                    models.DictionaryWord.id.in_(select(user_words_subq.c.id))
                )
            )

            # Фильтруем русские слова на Python уровне
            words_result = await db.scalars(stmt)
            all_ru_words = words_result.all()

            # Исключаем слова из exclude_translations
            filtered_words = [word for word in all_ru_words if word not in exclude_translations]

            # Берем случайные слова
            import random
            words = random.sample(filtered_words, min(count_words, len(filtered_words))) if filtered_words else []

        if not get_en_words:
            # Для русского режима мы уже получили слова выше
            lack_count_words = count_words - len(words)

            if lack_count_words > 0:
                # Дополняем случайными русскими словами из всего словаря
                all_ru_words_stmt = (
                    select(func.unnest(models.DictionaryWord.ru_words).label("random_ru_word"))
                )
                all_ru_words_result = await db.scalars(all_ru_words_stmt)
                all_ru_words = all_ru_words_result.all()

                # Фильтруем и берем дополнительные слова
                filtered_add_words = [word for word in all_ru_words
                                      if word not in exclude_translations and word not in words]

                if filtered_add_words:
                    add_words = random.sample(filtered_add_words, min(lack_count_words, len(filtered_add_words)))
                    words.extend(add_words)

            return words[:count_words]

        # Для английского режима продолжаем старую логику
        words_result = await db.scalars(stmt)
        words: list[str] = words_result.all()

        lack_count_words = count_words - len(words)

        if lack_count_words > 0:
            if exclude_translations:
                exclude_conditions = or_(*[
                    models.DictionaryWord.ru_words.any(translation)
                    for translation in exclude_translations
                ])

                words_with_common_translations = (
                    select(models.DictionaryWord.id)
                    .where(exclude_conditions)
                ).scalar_subquery()
            else:
                words_with_common_translations = select(None).where(False).scalar_subquery()

            add_stmt = (
                select(models.DictionaryWord.word)
                .filter(
                    models.DictionaryWord.word != exclude_word,
                    ~models.DictionaryWord.id.in_(words_with_common_translations),
                    models.DictionaryWord.word.notin_(words) if words else True
                )
                .limit(lack_count_words)
                .order_by(func.random())
            )

            add_words_result = await db.scalars(add_stmt)
            add_words = add_words_result.all()
            words.extend(add_words)

        return words[:count_words]