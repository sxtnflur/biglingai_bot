from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message
from bot.keyboards.credits import CreditsKeyboards
from bot.keyboards.mistakes import MistakesKeyboards
from bot.middlewares import DatabaseMiddleware
from bot.texts.base import BaseTexts
from bot.texts.chatting import ChattingTexts
from bot.keyboards.chatting import ChattingKeyboards
from depends import langlearning_openai_service, chat_history_service
from exceptions import CreditsOverException
from services.mistakes_service import MistakesService
from services.users_service import UsersService
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

router = Router()
router.message.middleware(DatabaseMiddleware())
router.callback_query.middleware(DatabaseMiddleware())


class ChattingStates(StatesGroup):
    chatting = State()


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
    await call.message.delete_reply_markup()

    await call.message.answer(
        ChattingTexts.INSTRUCTION,
        reply_markup=ChattingKeyboards.start()
    )


@router.callback_query(F.data == 'chatting_mode_start')
async def chatting_mode_start(
    call: CallbackQuery, state: FSMContext, db: AsyncSession
):
    if not await UsersService(db).do_paid_action(call.from_user.id, credits=1):
        await call.message.answer(
            BaseTexts.CREDITS_OVER,
            reply_markup=CreditsKeyboards.go_to_credits_shop()
        )
        return

    await state.clear()
    answer = await langlearning_openai_service.send_text_talking(
        'Choose a topic yourself and start this dialog!',
        response_type='text'
    )
    try:
        await call.message.delete_reply_markup()
    except: pass
    await call.message.answer(
        ChattingTexts.ai_answer(answer),
        reply_markup=ChattingKeyboards.ai_answer()
    )
    await state.set_state(ChattingStates.chatting)
    await state.update_data(dialog_uuid=uuid.uuid4())


@router.message(ChattingStates.chatting, F.text)
async def chatting(
    message: Message, state: FSMContext,
    db: AsyncSession
):
    CHAT_TYPE = 'text-chatting'
    messages = await chat_history_service.get_history(
        user_id=message.from_user.id, chat_type=CHAT_TYPE
    )

    answer = await langlearning_openai_service.send_text_talking(
        message.text,
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
    if answer.result.indications:
        dialog_uuid = await state.get_value('dialog_uuid')
        await MistakesService(db).save_mistakes(
            user_id=message.from_user.id,
            dialog_uuid=dialog_uuid,
            mistakes=answer.result.indications,
            user_message=message.text
        )

    if len(messages) >= 8:
        dialog_uuid = await state.get_value('dialog_uuid')
        await state.clear()
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