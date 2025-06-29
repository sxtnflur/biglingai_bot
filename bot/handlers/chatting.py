import os
import random

from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message, ReactionTypeUnion, ReactionTypeEmoji, BufferedInputFile
from bot.callbacks.chatting import SelectChattingTypeCallback
from bot.keyboards.credits import CreditsKeyboards
from bot.keyboards.mistakes import MistakesKeyboards
from bot.middlewares import DatabaseMiddleware
from bot.texts.base import BaseTexts
from bot.texts.chatting import ChattingTexts
from bot.keyboards.chatting import ChattingKeyboards
from bot.utils.media import save_voice_as_mp3
from depends import langlearning_openai_service, chat_history_service
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
    type_: Literal['text', 'audio', 'text-and-audio']
) -> None:
    if answer.result.answer.audio:
        if type_ == 'text-and-audio':
            await message.answer_voice(
                voice=BufferedInputFile(answer.result.answer.audio, filename='voice.mp3'),
                caption=ChattingTexts.ai_answer(answer),
                reply_markup=ChattingKeyboards.ai_answer()
            )
        elif type_ == 'audio':
            await message.answer_voice(
                voice=BufferedInputFile(answer.result.answer.audio, filename='voice.mp3'),
                caption=ChattingTexts.ai_answer_mistakes(answer.result),
                reply_markup=ChattingKeyboards.ai_answer()
            )
        else:
            await message.answer(
                ChattingTexts.ai_answer(answer),
                reply_markup=ChattingKeyboards.ai_answer()
            )
    else:
        await message.answer(
            ChattingTexts.ai_answer(answer),
            reply_markup=ChattingKeyboards.ai_answer()
        )


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
        'Hello!', theme=theme, dialog_type=dialog_type, voice_over=False
    )
    try:
        await call.message.edit_text(
            text=call.message.text + '\n{}\n<i>{}</i>'.format(ChattingTexts.dialog_type_label(dialog_type), theme),
            reply_markup=None
        )
    except: pass

    type_: Literal['text', 'audio', 'text-and-audio'] = 'text-and-audio'
    await send_ai_message(answer, call.message, type_=type_)

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

    if message.voice:
        path_to_audio = await save_voice_as_mp3(message.voice)
        answer = await langlearning_openai_service.send_audio_talking(
            path_to_audio=path_to_audio,
            dialog_type=dialog_type,
            theme=theme,
            messages=messages,
            voice_over=False
        )
        os.remove(path_to_audio)
    else:
        answer = await langlearning_openai_service.send_text_talking(
            message.text,
            dialog_type=dialog_type,
            theme=theme,
            messages=messages,
            voice_over=False
        )
    type_: Literal['text', 'audio', 'text-and-audio'] = 'text-and-audio'
    await send_ai_message(answer=answer, message=message, type_=type_)

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
    dialog_uuid = None
    print(f"{answer.result.indications=}")
    if answer.result.indications:
        dialog_uuid = await state.get_value('dialog_uuid')
        mistakes_service = MistakesService(db)
        await mistakes_service.add_mistake_groups_if_not_exist(
            list(map(lambda x: {'key': x.type, 'name': x.group}, answer.result.indications))
        )
        await mistakes_service.save_mistakes(
            user_id=message.from_user.id,
            dialog_uuid=dialog_uuid,
            mistakes=answer.result.indications,
            user_message=message.text
        )

    reaction = get_reaction(len(answer.result.indications) if answer.result.indications else 0)
    if reaction:
        await message.react([reaction], is_big=False)

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