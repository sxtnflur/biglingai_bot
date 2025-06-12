from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message
from bot.callbacks.translator import TranslateThisPhraseCallback
from bot.keyboards.credits import CreditsKeyboards
from bot.middlewares import DatabaseMiddleware
from bot.texts.base import BaseTexts
from bot.texts.translation import TranslationTexts
from depends import translator as translator_service
from bot.keyboards.base import BaseKeyboards
from services.users_service import UsersService
from sqlalchemy.ext.asyncio import AsyncSession

router = Router()
router.message.middleware(DatabaseMiddleware())
router.callback_query.middleware(DatabaseMiddleware())


class TranslatorStates(StatesGroup):
    get_text_to_translate = State()


@router.callback_query(F.data == 'translator')
async def translator(
    call: CallbackQuery, state: FSMContext
):
    await state.clear()
    await call.message.edit_text(TranslationTexts.MAIN, reply_markup=BaseKeyboards.create_kb_back('start'))
    await state.set_state(TranslatorStates.get_text_to_translate)


@router.message(TranslatorStates.get_text_to_translate)
async def get_text_to_translate(
    m: Message, db: AsyncSession
):
    if not await UsersService(db).do_paid_action(m.from_user.id, credits=1):
        await m.answer(
            BaseTexts.CREDITS_OVER,
            reply_markup=CreditsKeyboards.go_to_credits_shop()
        )
        return
    phrase = m.text
    translation = await translator_service.translate(text=phrase)
    await m.answer(TranslationTexts.show_translation(phrase, translation), reply_markup=BaseKeyboards.create_kb_back('start'))


@router.callback_query(TranslateThisPhraseCallback.filter())
async def translate_this_phrase(
    call: CallbackQuery, callback_data: TranslateThisPhraseCallback,
    db: AsyncSession
):
    if not await UsersService(db).do_paid_action(call.from_user.id, credits=1):
        await call.message.answer(
            BaseTexts.CREDITS_OVER,
            reply_markup=CreditsKeyboards.go_to_credits_shop()
        )
        return

    phrase = call.message.html_text[callback_data.from_index:callback_data.to_index]
    print(f'{phrase=}')
    translation = await translator_service.translate(text=phrase)
    await call.message.answer(TranslationTexts.show_translation(phrase, translation),
                              reply_markup=BaseKeyboards.create_kb_back('start'))