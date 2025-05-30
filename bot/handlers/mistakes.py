from uuid import UUID

from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from bot.callbacks.mistakes import MistakesListCallback, MistakeGroupListCallback, MistakeCallback, \
    TrainMistakeGroupCallback, TrainMistakeGroupAnswerCallback, MistakesListByDialogCallback
from bot.keyboards.mistakes import MistakesKeyboards
from exceptions import CreditsOverException
from schemas.chatting import MistakeSubGroup
from services.users_service import UsersService
from sqlalchemy.ext.asyncio import AsyncSession
from services.mistakes_service import MistakesService
from ..keyboards.credits import CreditsKeyboards
from ..middlewares import DatabaseMiddleware
from ..texts.base import BaseTexts
from ..texts.mistakes import MistakesTexts
from depends import langlearning_openai_service

router = Router()
router.callback_query.middleware(DatabaseMiddleware())


@router.callback_query(MistakesListCallback.filter())
async def mistakes(
    call: CallbackQuery,
    callback_data: MistakesListCallback,
    db: AsyncSession
):
    groups = await MistakesService(db).get_user_mistake_groups(
        user_id=call.from_user.id,
        offset=callback_data.page * callback_data.limit,
        limit=callback_data.limit
    )
    reply_markup = MistakesKeyboards.mistake_groups_list(
        groups=groups, limit=callback_data.limit,
        page=callback_data.page
    )
    if groups:
        text = MistakesTexts.GROUPS_IF_HAS_MISTAKES
    else:
        text = MistakesTexts.GROUPS_IF_NO_MISTAKES

    await call.message.edit_text(
        text=text,
        reply_markup=reply_markup
    )


@router.callback_query(MistakeGroupListCallback.filter())
async def mistake_group(
    call: CallbackQuery,
    callback_data: MistakeGroupListCallback,
    db: AsyncSession
):
    mistakes = await MistakesService(db).get_mistakes(
        user_id=call.from_user.id, by_subgroup=MistakeSubGroup(callback_data.group),
        offset=callback_data.page * callback_data.limit,
        limit=callback_data.limit
    )
    await call.message.edit_text(
        text=MistakesTexts.MISTAKES_LIST,
        reply_markup=MistakesKeyboards.mistakes_list(
            mistakes=mistakes,
            group=MistakeSubGroup(callback_data.group),
            limit=callback_data.limit,
            page=callback_data.page
        )
    )



@router.callback_query(MistakeCallback.filter())
async def get_mistake(
    call: CallbackQuery,
    callback_data: MistakeCallback,
    db: AsyncSession
):
    mistake = await MistakesService(db).get_mistake(callback_data.id)
    await call.message.edit_text(
        MistakesTexts.mistake(mistake),
        reply_markup=MistakesKeyboards.mistake(group=mistake.subgroup)
    )


@router.callback_query(TrainMistakeGroupCallback.filter())
async def train_mistake_group(
    call: CallbackQuery, callback_data: TrainMistakeGroupCallback,
    db: AsyncSession
):
    if not await UsersService(db).do_paid_action(user_tid=call.from_user.id, credits=1):
        await call.message.answer(
            BaseTexts.CREDITS_OVER,
            reply_markup=CreditsKeyboards.go_to_credits_shop()
        )
        return

    random_mistake = await MistakesService(db).get_random_mistake(
        user_id=call.from_user.id, by_group=MistakeSubGroup(callback_data.group)
    )
    prompt = (f'Придумай задание для того, чтобы отточить ошибки из группы {random_mistake.subgroup.subgroup_label}. '
              f'Пример ошибки: {random_mistake.user_message}. '
              f'Пояснение к ошибке: {random_mistake.explanation}')
    print(f'{prompt=}')
    task = await langlearning_openai_service.choose_one_variant(prompt=prompt)
    await call.message.edit_text(
        task.task,
        reply_markup=MistakesKeyboards.train_mistake_choice(
            choices=task.choices, mistake_id=random_mistake.id,
            group=MistakeSubGroup(callback_data.group)
        )
    )


@router.callback_query(TrainMistakeGroupAnswerCallback.filter())
async def train_mistake_answer(
    call: CallbackQuery,
    callback_data: TrainMistakeGroupAnswerCallback,
    db: AsyncSession
):
    right_answer = None
    for btns in call.message.reply_markup.inline_keyboard:
        for btn in btns:
            print(f'{btn=}')
            answer_callback = TrainMistakeGroupAnswerCallback.from_callback_data(btn.callback_data)
            print(f'{answer_callback=}')
            if answer_callback:
                print(f'+ {answer_callback=}')
                if answer_callback.is_right:
                    print(f'++ {answer_callback=}')
                    right_answer = btn.text
                    break
    print(f'{right_answer=}')
    if callback_data.is_right:
        text = MistakesTexts.TRAIN_MISTAKES_ANSWER_IF_RIGHT
    else:
        text = MistakesTexts.train_mistakes_answer_if_wrong(right_answer)

    await call.message.delete_reply_markup()
    await call.message.edit_text(
        text=call.message.text + '\n\n<b>Правильный ответ:</b> {}'.format(right_answer),
        parse_mode=ParseMode.HTML
    )

    await call.message.answer(text)

    try:
        await UsersService(db).update_user_credits(
            user_tid=call.from_user.id, credits=1, action='down'
        )
    except CreditsOverException:
        await call.message.edit_text(
            BaseTexts.CREDITS_OVER,
            reply_markup=CreditsKeyboards.go_to_credits_shop()
        )
        return

    random_mistake = await MistakesService(db).get_random_mistake(
        user_id=call.from_user.id, by_group=MistakeSubGroup(callback_data.group)
    )
    prompt = (f'Придумай задание для того, чтобы отточить ошибки из группы {random_mistake.subgroup.subgroup_label}. '
               f'Пример ошибки: {random_mistake.user_message}. '
               f'Пояснение к ошибке: {random_mistake.explanation}')
    print(f'{prompt=}')
    task = await langlearning_openai_service.choose_one_variant(
        prompt=prompt
    )
    await call.message.answer(
        task.task,
        reply_markup=MistakesKeyboards.train_mistake_choice(
            choices=task.choices, mistake_id=random_mistake.id,
            group=MistakeSubGroup(callback_data.group)
        )
    )


@router.callback_query(MistakesListByDialogCallback.filter())
async def mistakes_by_dialog(
    call: CallbackQuery, callback_data: MistakesListByDialogCallback,
    db: AsyncSession
):
    mistakes = await MistakesService(db).get_mistakes(
        user_id=call.from_user.id,
        by_dialog_uuid=UUID(callback_data.dialog_uuid),
        offset=callback_data.page * callback_data.limit,
        limit=callback_data.limit
    )
    await call.message.edit_text(
        text=MistakesTexts.MISTAKES_LIST,
        reply_markup=MistakesKeyboards.mistakes_list_by_dialog_uuid(
            mistakes=mistakes,
            dialog_uuid=callback_data.dialog_uuid,
            limit=callback_data.limit,
            page=callback_data.page
        )
    )