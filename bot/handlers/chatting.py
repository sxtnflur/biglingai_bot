import random

from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message, ReactionTypeUnion, ReactionTypeEmoji
from bot.callbacks.chatting import SelectChattingTypeCallback
from bot.keyboards.credits import CreditsKeyboards
from bot.keyboards.mistakes import MistakesKeyboards
from bot.middlewares import DatabaseMiddleware
from bot.texts.base import BaseTexts
from bot.texts.chatting import ChattingTexts
from bot.keyboards.chatting import ChattingKeyboards
from depends import langlearning_openai_service, chat_history_service
from exceptions import CreditsOverException
from schemas.chatting import DialogType
from services.mistakes_service import MistakesService
from services.users_service import UsersService
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from bot import utils

router = Router()
router.message.middleware(DatabaseMiddleware())
router.callback_query.middleware(DatabaseMiddleware())


class ChattingStates(StatesGroup):
    chatting = State()

CHAT_TYPE = f'text-chatting'


def get_reaction(count_mistakes: int) -> ReactionTypeUnion | None:
    if not count_mistakes:
        return utils.get_reaction_by_level(is_positive=True)


@router.callback_query(F.data == 'choose_mode:chatting')
async def start_chatting(
    call: CallbackQuery, state: FSMContext, db: AsyncSession
):
    if not await UsersService(db).check_access_to_paid_action(call.from_user.id, credits=1):
        await call.message.edit_text(
            BaseTexts.CREDITS_OVER,
            reply_markup=CreditsKeyboards.go_to_credits_shop()
        )
        return

    await state.clear()

    await call.message.edit_text(
        ChattingTexts.INSTRUCTION,
        reply_markup=ChattingKeyboards.select_chatting_type()
    )


@router.callback_query(SelectChattingTypeCallback.filter())
async def chatting_mode_start(
    call: CallbackQuery, state: FSMContext, db: AsyncSession,
    callback_data: SelectChattingTypeCallback
):
    if not await UsersService(db).do_paid_action(call.from_user.id, credits=1):
        await call.message.answer(
            BaseTexts.CREDITS_OVER,
            reply_markup=CreditsKeyboards.go_to_credits_shop()
        )
        return

    await state.clear()
    dialog_type = DialogType(callback_data.type)
    theme = dialog_type.random_theme
    answer = await langlearning_openai_service.send_text_talking(
        'Hello!', theme=theme, dialog_type=dialog_type, response_type='text'
    )
    try:
        await call.message.edit_text(
            text=call.message.text + '\n{}\n<i>{}</i>'.format(ChattingTexts.dialog_type_label(dialog_type), theme),
            reply_markup=None
        )
    except: pass
    await call.message.answer(
        ChattingTexts.ai_answer(answer),
        reply_markup=ChattingKeyboards.ai_answer()
    )
    await state.set_state(ChattingStates.chatting)
    await state.update_data(dialog_uuid=uuid.uuid4(), dialog_type=callback_data.type, theme=theme)

    await chat_history_service.clear_history(
        user_id=call.from_user.id,
        chat_type=CHAT_TYPE
    )
    await chat_history_service.add_message_to_history(
        message={'role': 'assistant', 'content': answer.result.answer.text},
        user_id=call.from_user.id,
        chat_type=CHAT_TYPE
    )


@router.message(ChattingStates.chatting, F.text)
async def chatting(
    message: Message, state: FSMContext,
    db: AsyncSession
):
    messages = await chat_history_service.get_history(
        user_id=message.from_user.id, chat_type=CHAT_TYPE
    )
    data = await state.get_data()

    dialog_type = data.get('dialog_type')
    dialog_type = DialogType(dialog_type)
    theme = data.get('theme')

    answer = await langlearning_openai_service.send_text_talking(
        message.text,
        dialog_type=dialog_type,
        theme=theme,
        messages=messages,
        response_type='text'
    )
    await message.answer(
        ChattingTexts.ai_answer(answer),
        parse_mode=ParseMode.HTML,
        reply_markup=ChattingKeyboards.ai_answer()
    )
    if not await UsersService(db).do_paid_action(message.from_user.id, credits=1):
        await message.answer(
            BaseTexts.CREDITS_OVER,
            reply_markup=CreditsKeyboards.go_to_credits_shop()
        )
        return
    if not answer.is_right_lang:
        return

    await chat_history_service.add_messages_to_history(
        user_message={'role': 'user', 'content': message.text},
        assistant_message={'role': 'assistant', 'content': answer.result.answer.text},
        user_id=message.from_user.id,
        chat_type=CHAT_TYPE
    )
    dialog_uuid = None

    if answer.result.indications:
        dialog_uuid = await state.get_value('dialog_uuid')
        await MistakesService(db).save_mistakes(
            user_id=message.from_user.id,
            dialog_uuid=dialog_uuid,
            mistakes=answer.result.indications,
            user_message=message.text
        )

    reaction = get_reaction(len(answer.result.indications) if answer.result.indications else 0)
    if reaction:
        await message.react([reaction], is_big=True)

    if answer.end_talking:
        await state.clear()
        if not dialog_uuid:
            dialog_uuid = await state.get_value('dialog_uuid')

        print(f'{dialog_uuid=}')
        mistakes = await MistakesService(db).get_mistakes(
            user_id=message.from_user.id,
            by_dialog_uuid=dialog_uuid
        )
        await message.answer(
            ChattingTexts.result_dialog(
                count_messages=len(messages),
                mistakes=mistakes
            ),
            reply_markup=MistakesKeyboards.result_chatting_dialog(
                dialog_uuid=dialog_uuid, has_mistakes=True if mistakes else False
            )
        )
        await chat_history_service.clear_history(
            user_id=message.from_user.id,
            chat_type=CHAT_TYPE
        )