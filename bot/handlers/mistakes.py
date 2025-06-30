from uuid import UUID

from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from bot.callbacks.mistakes import MistakesListCallback, MistakeGroupListCallback, MistakeCallback, \
    TrainMistakeGroupCallback, TrainMistakeGroupAnswerCallback, MistakesListByDialogCallback, DeleteMistakeCallback
from bot.keyboards.mistakes import MistakesKeyboards
from exceptions import CreditsOverException
from schemas.chatting import MistakeSubGroup
from services.ai.base import ResChoice
from services.users_service import UsersService
from sqlalchemy.ext.asyncio import AsyncSession
from services.mistakes_service import MistakesService
from .. import utils
from ..keyboards.credits import CreditsKeyboards
from ..middlewares import DatabaseMiddleware
from ..texts.base import BaseTexts
from ..texts.mistakes import MistakesTexts
from depends import langlearning_openai_service

router = Router()
router.callback_query.middleware(DatabaseMiddleware())


@router.callback_query(MistakesListCallback.filter())
async def mistakes_types_list_handler(
    call: CallbackQuery,
    callback_data: MistakesListCallback,
    db: AsyncSession
):
    groups = await MistakesService(db).get_user_mistake_groups(
        user_id=call.from_user.id,
        offset=callback_data.page * callback_data.limit,
        limit=callback_data.limit
    )
    count_worked_mistakes = await MistakesService(db).count_worked_out_mistakes(call.from_user.id)
    reply_markup = MistakesKeyboards.mistake_groups_list(
        groups=groups, limit=callback_data.limit,
        page=callback_data.page
    )
    if groups:
        text = MistakesTexts.groups_if_has_mistakes(
            count_worked_mistakes=count_worked_mistakes
        )
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
        user_id=call.from_user.id, by_type_key=callback_data.group.replace('&', ':'),
        offset=callback_data.page * callback_data.limit,
        limit=callback_data.limit
    )
    if not mistakes:
        await call.answer('В этой группе не осталось ошибок')
        await mistakes_types_list_handler(
            call=call,
            callback_data=MistakesListCallback(),
            db=db
        )
        return
    await call.message.edit_text(
        text=MistakesTexts.MISTAKES_LIST,
        reply_markup=MistakesKeyboards.mistakes_list(
            mistakes=mistakes,
            group=callback_data.group,
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
        reply_markup=MistakesKeyboards.mistake(type_key=mistake.type.key, mistake_id=callback_data.id)
    )


@router.callback_query(DeleteMistakeCallback.filter())
async def delete_mistake(
    call: CallbackQuery,
    callback_data: DeleteMistakeCallback,
    db: AsyncSession
):
    if callback_data.pre:
        await call.message.edit_text(
            MistakesTexts.SELECT_REASON_DELETE_MISTAKE,
            reply_markup=MistakesKeyboards.delete_mistake(mistake_id=callback_data.mistake_id)
        )
        return
    else:
        service = MistakesService(db)
        if callback_data.is_worked_out:
            mistake = await service.mark_mistake_as_worked_out(mistake_id=callback_data.mistake_id, user_id=call.from_user.id)
        elif callback_data.really_delete:
            mistake = await service.delete_mistake(mistake_id=callback_data.mistake_id, user_id=call.from_user.id)
        else:
            return

        await call.answer(f'Ошибка "{mistake.incorrect}" удалена')
        await mistake_group(
            call=call, callback_data=MistakeGroupListCallback(group=mistake.type_key),
            db=db
        )


async def create_train_mistake_group(
    user_id: int, group: str, db: AsyncSession
) -> dict:
    random_mistake = await MistakesService(db).get_random_mistake(
        user_id=user_id, by_type_key=group
    )
    prompt = (f'Придумай задание для того, чтобы отточить ошибки из группы {random_mistake.subgroup.subgroup_label}. '
              f'Пример ошибки: {random_mistake.user_message}. '
              f'Пояснение к ошибке: {random_mistake.explanation}')
    task = await langlearning_openai_service.choose_one_variant(prompt=prompt)
    return dict(
        text=MistakesTexts.train_mistakes_task(task=task.task, choices=task.enumerated_choices),
        reply_markup=MistakesKeyboards.train_mistake_choice(
            choices=task.enumerated_choices,
            mistake_id=random_mistake.id,
            group=group
        )
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

    message_data = await create_train_mistake_group(
        user_id=call.from_user.id,
        group=callback_data.group,
        db=db
    )
    await call.message.answer(**message_data)


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

    message_data = await create_train_mistake_group(
        user_id=call.from_user.id,
        group=callback_data.group,
        db=db
    )
    await call.message.answer(**message_data)


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