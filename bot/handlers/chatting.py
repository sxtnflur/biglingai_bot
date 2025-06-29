import os
import random

from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message, ReactionTypeUnion, ReactionTypeEmoji, BufferedInputFile
from bot.callbacks.chatting import SelectChattingTypeCallback, ChangeChattingMessageTypeCallback
from bot.keyboards.credits import CreditsKeyboards
from bot.keyboards.mistakes import MistakesKeyboards
from bot.middlewares import DatabaseMiddleware
from bot.texts.base import BaseTexts
from bot.texts.chatting import ChattingTexts
from bot.keyboards.chatting import ChattingKeyboards
from bot.utils.media import save_voice_as_mp3
from depends import langlearning_openai_service, chat_history_service
from enums import ChattingMessageType
from exceptions import CreditsOverException
from schemas.chatting import DialogType, TalkingResponse
from services.mistakes_service import MistakesService
from services.users_service import UsersService
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from bot import utils
from typing_extensions import Literal

router = Router()
router.message.middleware(DatabaseMiddleware())
router.callback_query.middleware(DatabaseMiddleware())


class ChattingStates(StatesGroup):
    chatting = State()

CHAT_TYPE = f'text-chatting'


def get_reaction(count_mistakes: int) -> ReactionTypeUnion | None:
    if not count_mistakes:
        return utils.get_reaction_by_level(is_positive=True)


async def send_ai_message(
    answer: TalkingResponse, message: Message,
    message_type: ChattingMessageType
) -> None:
    if not answer.is_right_lang:
        await message.answer(
            text=ChattingTexts.IF_IS_NOT_ENG_MESSAGE,
            reply_markup=ChattingKeyboards.ai_answer()
        )
        return
    if answer.result.answer.audio:
        if message_type == ChattingMessageType.text_and_voice:
            await message.answer_voice(
                voice=BufferedInputFile(answer.result.answer.audio, filename='voice.mp3'),
                caption=ChattingTexts.ai_answer(answer.result),
                reply_markup=ChattingKeyboards.ai_answer()
            )
        elif message_type == ChattingMessageType.voice:
            await message.answer_voice(
                voice=BufferedInputFile(answer.result.answer.audio, filename='voice.mp3'),
                caption=ChattingTexts.ai_answer_mistakes(answer.result.correction),
                reply_markup=ChattingKeyboards.ai_answer()
            )
        else:
            await message.answer(
                ChattingTexts.ai_answer(answer.result),
                reply_markup=ChattingKeyboards.ai_answer()
            )
    else:
        await message.answer(
            ChattingTexts.ai_answer(answer.result),
            reply_markup=ChattingKeyboards.ai_answer()
        )


async def end_dialog(state: FSMContext, dialog_uuid: uuid.UUID | None, db: AsyncSession, message: Message, messages: list[...]):
    await state.clear()
    if not dialog_uuid:
        dialog_uuid = await state.get_value('dialog_uuid')

    if len(messages) <= 5:
        await message.answer(
            ChattingTexts.NOT_ENOUGH_MESSAGES_TO_RATE_DIALOG,
            reply_markup=MistakesKeyboards.result_chatting_dialog(
                dialog_uuid=dialog_uuid, has_mistakes=False
            )
        )
        return

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


@router.callback_query(F.data == 'choose_mode:chatting')
async def start_chatting(
    call: CallbackQuery, state: FSMContext
):
    await state.set_state(None)
    await call.message.edit_text(
        ChattingTexts.INSTRUCTION,
        reply_markup=ChattingKeyboards.start(
            current_message_type=ChattingMessageType.text_and_voice
        )
    )


@router.callback_query(ChangeChattingMessageTypeCallback.filter())
async def change_chatting_message_type(
    call: CallbackQuery,
    callback_data: ChangeChattingMessageTypeCallback,
    state: FSMContext
):
    new_val = ChattingMessageType(callback_data.type).next()
    await state.update_data(chatting_message_type=new_val)
    await call.message.edit_text(
        ChattingTexts.INSTRUCTION,
        reply_markup=ChattingKeyboards.start(
            current_message_type=new_val
        )
    )


@router.callback_query(F.data == 'chatting_choose_mode')
async def chatting_choose_type(
    call: CallbackQuery, state: FSMContext, db: AsyncSession
):
    if not await UsersService(db).check_access_to_paid_action(call.from_user.id, credits=1):
        await call.message.edit_text(
            BaseTexts.CREDITS_OVER,
            reply_markup=CreditsKeyboards.go_to_credits_shop()
        )
        return

    await state.set_state(None)

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

    await state.set_state(None)
    dialog_type = DialogType(callback_data.type)
    theme = dialog_type.random_theme

    chatting_message_type = ChattingMessageType(
        await state.get_value(
            'chatting_message_type',
            ChattingMessageType.text_and_voice.value
        )
    )
    voice_over = False if chatting_message_type == ChattingMessageType.text else True
    answer = await langlearning_openai_service.send_text_talking(
        'Hello!', theme=theme, dialog_type=dialog_type, voice_over=voice_over
    )
    try:
        await call.message.edit_text(
            text=call.message.text + '\n{}\n<i>{}</i>'.format(ChattingTexts.dialog_type_label(dialog_type), theme),
            reply_markup=None
        )
    except: pass

    await send_ai_message(answer, call.message, message_type=chatting_message_type)

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


@router.message(ChattingStates.chatting, F.text | F.voice)
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
    dialog_uuid = data.get('dialog_uuid')
    chatting_message_type = ChattingMessageType(
        await state.get_value(
            'chatting_message_type',
            ChattingMessageType.text_and_voice.value
        )
    )

    if message.text == ChattingTexts.END_BUTTON:
        await end_dialog(
            state=state,
            message=message,
            messages=messages,
            db=db,
            dialog_uuid=dialog_uuid
        )
        return

    voice_over = False if chatting_message_type == ChattingMessageType.text else True
    if message.voice:
        path_to_audio = await save_voice_as_mp3(message.voice)
        answer = await langlearning_openai_service.send_audio_talking(
            path_to_audio=path_to_audio,
            dialog_type=dialog_type,
            theme=theme,
            messages=messages,
            voice_over=voice_over
        )
        os.remove(path_to_audio)
    else:
        answer = await langlearning_openai_service.send_text_talking(
            message.text,
            dialog_type=dialog_type,
            theme=theme,
            messages=messages,
            voice_over=voice_over
        )
    await send_ai_message(answer=answer, message=message, message_type=chatting_message_type)

    if not await UsersService(db).do_paid_action(message.from_user.id, credits=1):
        await message.answer(
            BaseTexts.CREDITS_OVER,
            reply_markup=CreditsKeyboards.go_to_credits_shop()
        )
        return
    if not answer.is_right_lang:
        return

    await chat_history_service.add_messages_to_history(
        user_message={'role': 'user', 'content': answer.result.original},
        assistant_message={'role': 'assistant', 'content': answer.result.answer.text},
        user_id=message.from_user.id,
        chat_type=CHAT_TYPE
    )

    if answer.result.correction:
        mistakes_service = MistakesService(db)
        await mistakes_service.add_mistake_groups_if_not_exist(
            list(map(lambda x: {'key': x.type, 'name': x.group}, answer.result.correction.mistakes))
        )
        await mistakes_service.save_mistakes(
            user_id=message.from_user.id,
            dialog_uuid=dialog_uuid,
            mistakes=answer.result.indications,
            user_message=message.text
        )

    reaction = get_reaction(len(answer.result.correction.mistakes) if answer.result.correction else 0)
    if reaction:
        await message.react([reaction], is_big=False)

    if answer.end_talking:
        await end_dialog(
            state, dialog_uuid, db, message, messages
        )