import random

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message
from bot.keyboards.credits import CreditsKeyboards
from bot.keyboards.dictionary import DictionaryKeyboards
from bot.keyboards.base import BaseKeyboards
from bot.middlewares import DatabaseMiddleware
from bot.texts.base import BaseTexts
from bot.texts.dictionary import DictionaryTexts
from depends import dictionary_service, translator
from services.users_service import UsersService
from sqlalchemy.ext.asyncio import AsyncSession
from bot.callbacks.dictionary import AddWordToDictCallback, MarkDictWordAsWorkedCallback, DictWordsListCallback

router = Router()


class DictionaryStates(StatesGroup):
    get_train_translate_word = State()



@router.callback_query(F.data == 'dictionary')
async def start_dictionary(
        call: CallbackQuery
):
    await call.message.edit_text(
        DictionaryTexts.MAIN,
        reply_markup=DictionaryKeyboards.main()
    )


@router.callback_query(F.data == 'how-to-add-word-to-dict')
async def how_to_add_word_to_dict(
        call: CallbackQuery
):
    await call.message.edit_text(
        DictionaryTexts.HOW_TO_ADD_WORD_INSTRUCTION,
        reply_markup=BaseKeyboards.create_kb_back('dictionary')
    )


router_ = Router()
router.include_router(router_)
router_.message.middleware(DatabaseMiddleware())
router_.callback_query.middleware(DatabaseMiddleware())


@router_.callback_query(AddWordToDictCallback.filter())
async def add_word_to_dict(
        call: CallbackQuery, callback_data: AddWordToDictCallback,
        db: AsyncSession, state: FSMContext
):
    await state.clear()
    if not await UsersService(db).do_paid_action(call.from_user.id, credits=1):
        await call.message.answer(
            BaseTexts.CREDITS_OVER,
            reply_markup=CreditsKeyboards.go_to_credits_shop()
        )
        return
    word = await dictionary_service.join_or_generate_word(
        word=callback_data.word, user_id=call.from_user.id, db=db
    )
    await call.message.edit_text(
        text=DictionaryTexts.word_is_added_to_dict(word),
        reply_markup=DictionaryKeyboards.word_is_added_to_dict()
    )


@router_.callback_query(F.data == 'train-my-dict')
async def dict_train(
        call: CallbackQuery, db: AsyncSession,
        state: FSMContext
):
    await state.clear()
    last_word = call.message.html_text[
                call.message.html_text.find('<blockquote>') + len('<blockquote>'):
                call.message.html_text.find('</blockquote>')
                ]
    count_available_words = await dictionary_service.count_user_dict_words(
        user_id=call.from_user.id, db=db,
        only_cant_be_worked=True, only_not_worked=True
    )

    # Если слов меньше 10, берем слово из чужого словаря с элементом рандома 50/50
    if count_available_words < 10 and random.randint(0, 1):
        user_level = await dictionary_service.count_user_level(
            user_id=call.from_user.id, db=db
        )
        word = await dictionary_service.get_random_word_from_dictionary(
            db=db,
            user_id=call.from_user.id,
            user_level=user_level,
            exclude_words=[last_word]
        )
        await dictionary_service.join_dictionary_word_to_user(
            word_id=word.id, user_id=call.from_user.id, db=db
        )
        learning_rate = 0
    else:
        word_data = await dictionary_service.get_random_user_word_from_dictionary(
            user_id=call.from_user.id, db=db, exclude_words=[last_word]
        )
        word = word_data.word
        learning_rate = word_data.user_info.learning_rate

    if word.word == last_word:
        return await dict_train(call, db)

    await call.message.delete_reply_markup()

    if learning_rate == 0:
        await dictionary_service.change_word_learning_rate(
            db=db, word_id=word.id, user_id=call.from_user.id,
            change_for_amount=1, increase=True
        )
        await call.message.answer(
            text=DictionaryTexts.word_remember_card(word),
            reply_markup=DictionaryKeyboards.train_card()
        )
    else:
        await call.message.answer(
            text=DictionaryTexts.word_remember_task(word=word.word),
            reply_markup=DictionaryKeyboards.exit()
        )
        await state.update_data(
            dict_train_translate_words=list(map(lambda x: x.lower(), word.ru_words)),
            dict_train_last_word=word.word,
            dict_train_last_word_id=word.id
        )
        await state.set_state(DictionaryStates.get_train_translate_word)


@router_.message(DictionaryStates.get_train_translate_word)
async def train_get_translate_word(
    m: Message, state: FSMContext, db: AsyncSession
):
    data = await state.get_data()
    dict_train_translate_words = data.get('dict_train_translate_words')
    last_word = data.get('dict_train_last_word')
    dict_train_last_word_id = data.get('dict_train_last_word_id')

    await state.clear()

    is_right = m.text.strip().lower() in dict_train_translate_words

    if is_right:
        await m.answer(
            text=DictionaryTexts.train_word_success(ru_words=dict_train_translate_words)
        )
    else:
        await m.answer(
            text=DictionaryTexts.train_word_wrong(ru_words=dict_train_translate_words)
        )

    # Изменяем рейтинг изучения юзера на этом слове
    updated_learning_rate = await dictionary_service.change_word_learning_rate(
        db=db, word_id=dict_train_last_word_id, user_id=m.from_user.id,
        change_for_amount=1, increase=is_right
    )

    # Если рейтинг изучения равен X, предлагаем отметить, как Отработанное
    if updated_learning_rate >= 7:
        await dictionary_service.mark_word_as_can_be_mark_as_worked(
            word_id=dict_train_last_word_id, user_id=m.from_user.id, db=db
        )
        await m.answer(
            text=DictionaryTexts.word_can_be_marked_as_worked(last_word),
            reply_markup=DictionaryKeyboards.word_can_be_marked_as_worked(word_id=dict_train_last_word_id)
        )

    word_data = await dictionary_service.get_random_user_word_from_dictionary(
        user_id=m.from_user.id, db=db, exclude_words=[last_word]
    )
    if not word_data:
        word = await dictionary_service.get_random_word_from_dictionary(
            db=db, user_id=m.from_user.id, user_level=1,
            exclude_words=[last_word]
        )
        await dictionary_service.join_dictionary_word_to_user(
            word_id=word.id, user_id=m.from_user.id, db=db
        )
        learning_rate = 0
        # can_be_mark_as_worked = False
    else:
        word = word_data.word
        # can_be_mark_as_worked = word_data.user_info.can_be_mark_as_worked
        learning_rate = word_data.user_info.learning_rate

    if learning_rate == 0:
        await dictionary_service.change_word_learning_rate(
            db=db, word_id=word.id, user_id=m.from_user.id,
            change_for_amount=1, increase=True
        )
        await m.answer(
            text=DictionaryTexts.word_remember_card(word),
            reply_markup=DictionaryKeyboards.train_card()
        )
    else:
        await m.answer(
            text=DictionaryTexts.word_remember_task(word=word.word),
            reply_markup=DictionaryKeyboards.exit()
        )
        await state.update_data(
            dict_train_translate_words=list(map(lambda x: x.lower(), word.ru_words)),
            dict_train_last_word=word.word,
            dict_train_last_word_id=word.id
        )
        await state.set_state(DictionaryStates.get_train_translate_word)


@router_.callback_query(MarkDictWordAsWorkedCallback.filter())
async def mark_word_as_worked(
    call: CallbackQuery, callback_data: MarkDictWordAsWorkedCallback,
    db: AsyncSession
):
    await dictionary_service.mark_word_as_worked(word_id=callback_data.word_id, user_id=call.from_user.id, db=db)
    await call.message.edit_text('Слово помечено как отработанное', reply_markup=None)

    if callback_data.from_training:
        pass


@router_.callback_query(DictWordsListCallback.filter())
async def dict_words_list(
    call: CallbackQuery, callback_data: DictWordsListCallback, db: AsyncSession
):
    if callback_data.change_order:
        call_text = 'Слова отсортированы '
        if callback_data.order_by == 'alphabet':
            call_text += 'по алфавиту '
        elif callback_data.order_by == 'learning_rate':
            call_text += 'по вашему уровню знания'

        if callback_data.order_asc:
            call_text += ' по возрастанию'
        else:
            call_text += ' по убыванию'
        await call.answer(call_text)

    count_words = await dictionary_service.count_user_dictionary_words(
        user_id=call.from_user.id, db=db
    )
    if not count_words:
        await call.answer('У вас пока нет слов в словаре. Зайдите в ➕, чтобы узнать как их добавить', show_alert=True)
        return

    words = await dictionary_service.get_user_dictionary_words(
        user_id=call.from_user.id, db=db,
        offset=callback_data.page * callback_data.limit,
        limit=callback_data.limit,
        order_by=callback_data.order_by,
        order_asc=callback_data.order_asc
    )

    await call.message.edit_text(
        text=DictionaryTexts.dict_words_list(user_words=words),
        reply_markup=DictionaryKeyboards.dict_words_list(
            page=callback_data.page, limit=callback_data.limit,
            last_page=(count_words // callback_data.limit),
            order_by=callback_data.order_by,
            order_asc=callback_data.order_asc
        )
    )