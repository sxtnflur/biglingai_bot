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
from bot.callbacks.dictionary import AddWordToDictCallback, MarkDictWordAsWorkedCallback

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
        db: AsyncSession
):
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
    last_word = call.message.html_text[
                call.message.html_text.find('<blockquote>') + len('<blockquote>'):
                call.message.html_text.find('</blockquote>')
                ]

    word_data = await dictionary_service.get_random_user_word_from_dictionary(
        user_id=call.from_user.id, db=db, exclude_words=[last_word]
    )
    if not word_data:
        word = await dictionary_service.get_random_word_from_dictionary(
            db=db, user_id=call.from_user.id, user_level=1,
            exclude_words=[last_word]
        )
        await dictionary_service.join_dictionary_word_to_user(
            word_id=word.id, user_id=call.from_user.id, db=db
        )
        learning_rate = 0
    else:
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
            dict_train_translate_word=word.ru_word,
            dict_train_last_word=word.word,
            dict_train_last_word_id=word.id
        )
        await state.set_state(DictionaryStates.get_train_translate_word)


@router_.message(DictionaryStates.get_train_translate_word)
async def train_get_translate_word(
    m: Message, state: FSMContext, db: AsyncSession
):
    data = await state.get_data()
    dict_train_translate_word = data.get('dict_train_translate_word')
    last_word = data.get('dict_train_last_word')
    dict_train_last_word_id = data.get('dict_train_last_word_id')

    await state.clear()

    is_right = m.text.strip().lower() == dict_train_translate_word.lower()

    if is_right:
        await m.answer(
            text=DictionaryTexts.train_word_success(ru_word=dict_train_translate_word)
        )
    else:
        await m.answer(
            text=DictionaryTexts.train_word_wrong(ru_word=dict_train_translate_word)
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
            dict_train_translate_word=word.ru_word,
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