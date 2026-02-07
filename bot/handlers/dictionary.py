import datetime
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
from database.decorator import db_connect
from depends import dictionary_service, translator, scheduler
from services.users_service import UsersService
from sqlalchemy.ext.asyncio import AsyncSession
from bot.callbacks.dictionary import AddWordToDictCallback, MarkDictWordAsWorkedCallback, DictWordsListCallback, \
    TrainDictCallback, SelectWordTranslationCallback

router = Router()


class DictionaryStates(StatesGroup):
    get_train_translate_word = State()


@router.callback_query(F.data == 'how-to-add-word-to-dict')
async def how_to_add_word_to_dict(
        call: CallbackQuery
):
    await call.message.edit_text(
        DictionaryTexts.HOW_TO_ADD_WORD_INSTRUCTION,
        reply_markup=BaseKeyboards.create_kb_back('dictionary')
    )


@db_connect()
async def start_dictionary_message(
        message: Message, *, db: AsyncSession
):
    count_total_worked_words = await dictionary_service.count_user_dict_words(
        user_id=message.from_user.id, db=db,
        can_be_mark_as_worked=True
    )
    count_already_know_words = await dictionary_service.count_user_dict_words(
        user_id=message.from_user.id, db=db,
        can_be_mark_as_worked=True, already_know=True
    )
    count_worked_in_bot_words = await dictionary_service.count_user_dict_words(
        user_id=message.from_user.id, db=db,
        can_be_mark_as_worked=True, already_know=False
    )
    await message.answer(
        DictionaryTexts.main(
            count_total_worked_words, count_worked_in_bot_words, count_already_know_words
        ),
        reply_markup=DictionaryKeyboards.main()
    )


@router.callback_query(F.data == 'dictionary')
@db_connect()
async def start_dictionary(
        call: CallbackQuery, *, db: AsyncSession
):
    count_total_worked_words = await dictionary_service.count_user_dict_words(
        user_id=call.from_user.id, db=db,
        can_be_mark_as_worked=True
    )
    count_already_know_words = await dictionary_service.count_user_dict_words(
        user_id=call.from_user.id, db=db,
        can_be_mark_as_worked=True, already_know=True
    )
    count_worked_in_bot_words = await dictionary_service.count_user_dict_words(
        user_id=call.from_user.id, db=db,
        can_be_mark_as_worked=True, already_know=False
    )
    await call.message.edit_text(
        DictionaryTexts.main(
            count_total_worked_words, count_worked_in_bot_words, count_already_know_words
        ),
        reply_markup=DictionaryKeyboards.main()
    )


@router.callback_query(AddWordToDictCallback.filter())
@db_connect()
async def add_word_to_dict(
        call: CallbackQuery, callback_data: AddWordToDictCallback,
        state: FSMContext, *, db: AsyncSession
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


@db_connect()
async def get_message_train_word(user_id: int, state: FSMContext, last_word: str,
                                 *, db: AsyncSession):
    word, learning_rate = await dictionary_service.get_randow_word_to_train(
        user_id=user_id, db=db, last_word=last_word
    )
    print(f'{word=} {learning_rate=}')

    if word.word == last_word:
        return await get_message_train_word(user_id, state, db, last_word)

    if learning_rate == 0:
        await dictionary_service.change_word_learning_rate(
            db=db, word_id=word.id, user_id=user_id,
            change_for_amount=1, increase=True
        )
        return dict(
            text=DictionaryTexts.word_remember_card(word),
            reply_markup=DictionaryKeyboards.train_card()
        )
    elif learning_rate < 4:
        en_words = random.randint(0, 1)
        wrong_words = await dictionary_service.get_wrong_words(
            user_id=user_id, exclude_word=word.word, db=db, get_en_words=en_words
        )
        await state.update_data(
            dict_train_translate_words=[word.word],
            dict_train_last_word=word.word,
            dict_train_last_word_id=word.id
        )
        orig_word = word.word if not en_words else random.choice(word.ru_words)
        return dict(
            text=DictionaryTexts.select_right_translation(orig_word),
            reply_markup=DictionaryKeyboards.select_right_translation(
                right_word=word.word if en_words else random.choice(word.ru_words),
                wrong_words=wrong_words
            )
        )
    else:
        await state.update_data(
            dict_train_translate_words=list(map(lambda x: x.lower(), word.ru_words)),
            dict_train_last_word=word.word,
            dict_train_last_word_id=word.id
        )
        await state.set_state(DictionaryStates.get_train_translate_word)
        return dict(
            text=DictionaryTexts.word_remember_task(word=word.word),
            reply_markup=DictionaryKeyboards.exit()
        )


@router.callback_query(TrainDictCallback.filter())
@db_connect()
async def dict_train(
        call: CallbackQuery,
        state: FSMContext, callback_data: TrainDictCallback,
        *, db: AsyncSession
):
    await state.clear()
    last_word = call.message.html_text[
                call.message.html_text.find('<blockquote>') + len('<blockquote>'):
                call.message.html_text.find('</blockquote>')
                ]

    if callback_data.already_know:
        await dictionary_service.mark_word_as_already_know(
            word=last_word, user_id=call.from_user.id, db=db
        )

    await call.message.delete()
    await call.message.answer(
        **await get_message_train_word(
            user_id=call.from_user.id, state=state, db=db, last_word=last_word
        )
    )


@router.message(DictionaryStates.get_train_translate_word)
@db_connect()
async def train_get_translate_word(
    m: Message, state: FSMContext, *, db: AsyncSession
):
    data = await state.get_data()
    dict_train_translate_words = data.get('dict_train_translate_words')
    last_word = data.get('dict_train_last_word')
    dict_train_last_word_id = data.get('dict_train_last_word_id')

    await state.clear()

    is_right = m.text.strip().lower() in dict_train_translate_words

    if is_right:
        answer_msg = await m.answer(
            text=DictionaryTexts.train_word_success(ru_words=dict_train_translate_words)
        )
    else:
        answer_msg = await m.answer(
            text=DictionaryTexts.train_word_wrong(ru_words=dict_train_translate_words)
        )

    scheduler.scheduler.add_job(
        func=m.bot.delete_messages,
        kwargs=dict(chat_id=m.chat.id, message_ids=[answer_msg.message_id, m.message_id, m.message_id - 1]),
        trigger='date',
        run_date=datetime.datetime.now() + datetime.timedelta(seconds=3)
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

    await m.answer(
        **await get_message_train_word(
            user_id=m.from_user.id, db=db, state=state, last_word=last_word
        )
    )


@router.callback_query(SelectWordTranslationCallback.filter())
@db_connect()
async def select_word_translation(
    call: CallbackQuery, callback_data: SelectWordTranslationCallback,
    state: FSMContext, *, db: AsyncSession
):
    data = await state.get_data()
    dict_train_translate_words = data.get('dict_train_translate_words')
    last_word = data.get('dict_train_last_word')
    dict_train_last_word_id = data.get('dict_train_last_word_id')

    await state.clear()

    if callback_data.right:
        answer_msg = await call.message.edit_text(
            text=DictionaryTexts.train_word_success(ru_words=dict_train_translate_words)
        )
    else:
        answer_msg = await call.message.edit_text(
            text=DictionaryTexts.train_word_wrong(ru_words=dict_train_translate_words)
        )

    scheduler.scheduler.add_job(
        func=call.bot.delete_messages,
        kwargs=dict(chat_id=call.message.chat.id, message_ids=[answer_msg.message_id, call.message.message_id]),
        trigger='date',
        run_date=datetime.datetime.now() + datetime.timedelta(seconds=3)
    )

    # Изменяем рейтинг изучения юзера на этом слове
    updated_learning_rate = await dictionary_service.change_word_learning_rate(
        db=db, word_id=dict_train_last_word_id, user_id=call.from_user.id,
        change_for_amount=1, increase=callback_data.right
    )

    # Если рейтинг изучения равен X, предлагаем отметить, как Отработанное
    if updated_learning_rate >= 7:
        await dictionary_service.mark_word_as_can_be_mark_as_worked(
            word_id=dict_train_last_word_id, user_id=call.from_user.id, db=db
        )
        await call.message.answer(
            text=DictionaryTexts.word_can_be_marked_as_worked(last_word),
            reply_markup=DictionaryKeyboards.word_can_be_marked_as_worked(word_id=dict_train_last_word_id)
        )

    await call.message.answer(
        **await get_message_train_word(
            user_id=call.from_user.id, db=db, state=state, last_word=last_word
        )
    )


@router.callback_query(MarkDictWordAsWorkedCallback.filter())
@db_connect()
async def mark_word_as_worked(
    call: CallbackQuery, callback_data: MarkDictWordAsWorkedCallback, *,
    db: AsyncSession
):
    await dictionary_service.mark_word_as_worked(word_id=callback_data.word_id, user_id=call.from_user.id, db=db)
    msg = await call.message.edit_text('Слово помечено как отработанное', reply_markup=None)

    if callback_data.from_training:
        pass

    scheduler.scheduler.add_job(
        func=call.bot.delete_message,
        kwargs=dict(chat_id=call.message.chat.id, message_id=msg.message_id),
        trigger='date',
        run_date=datetime.datetime.now() + datetime.timedelta(seconds=3)
    )


@router.callback_query(DictWordsListCallback.filter())
@db_connect()
async def dict_words_list(
    call: CallbackQuery, callback_data: DictWordsListCallback, *, db: AsyncSession
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
        text=DictionaryTexts.dict_words_list(
            user_words=words
        ),
        reply_markup=DictionaryKeyboards.dict_words_list(
            page=callback_data.page, limit=callback_data.limit,
            last_page=(count_words // callback_data.limit),
            order_by=callback_data.order_by,
            order_asc=callback_data.order_asc
        )
    )