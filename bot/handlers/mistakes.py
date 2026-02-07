from datetime import datetime
from uuid import UUID

from aiogram import Router, F, Bot
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, Poll, PollAnswer
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
from ..keyboards.base import BaseKeyboards
from ..keyboards.credits import CreditsKeyboards
from ..middlewares import DatabaseMiddleware
from ..texts.base import BaseTexts
from ..texts.mistakes import MistakesTexts
from depends import langlearning_openai_service
from database.decorator import db_connect
from ..utils.do_while import send_action_while_do_func

router = Router()


@db_connect()
async def mistakes_list(m: Message, *, db: AsyncSession):
    groups = await MistakesService(db).get_user_mistake_groups(
        user_id=m.from_user.id,
        offset=0,
        limit=10
    )
    count_worked_mistakes = await MistakesService(db).count_worked_out_mistakes(m.from_user.id)
    reply_markup = MistakesKeyboards.mistake_groups_list(
        groups=groups, limit=10, page=0
    )
    if groups:
        text = MistakesTexts.groups_if_has_mistakes(
            count_worked_mistakes=count_worked_mistakes
        )
    else:
        text = MistakesTexts.GROUPS_IF_NO_MISTAKES

    await m.answer(
        text=text,
        reply_markup=reply_markup
    )


@router.callback_query(MistakesListCallback.filter())
@db_connect()
async def mistakes_types_list_handler(
    call: CallbackQuery,
    callback_data: MistakesListCallback, *,
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

    try:
        await call.message.edit_text(
            text=text,
            reply_markup=reply_markup
        )
    except:
        await call.message.answer(
            text=text,
            reply_markup=reply_markup
        )


@router.callback_query(MistakeGroupListCallback.filter())
@db_connect()
async def mistake_group(
    call: CallbackQuery,
    callback_data: MistakeGroupListCallback,
    *,
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
@db_connect()
async def get_mistake(
    call: CallbackQuery,
    callback_data: MistakeCallback, *,
    db: AsyncSession
):
    mistake = await MistakesService(db).get_mistake(callback_data.id)
    await call.message.edit_text(
        MistakesTexts.mistake(mistake),
        reply_markup=MistakesKeyboards.mistake(type_key=mistake.type.key, mistake_id=callback_data.id)
    )


@router.callback_query(DeleteMistakeCallback.filter())
@db_connect()
async def delete_mistake(
    call: CallbackQuery,
    callback_data: DeleteMistakeCallback,
    *,
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


@db_connect()
async def create_train_mistake_group(
    user_id: int,
    by_group: str | None = None,
    by_dialog_uuid: str | None = None,
    *, db: AsyncSession | None = None
) -> dict:
    random_mistake = await MistakesService(db).get_random_mistake(
        user_id=user_id, by_type_key=by_group, by_dialog_uuid=by_dialog_uuid
    )
    prompt = (f'Придумай задание для того, чтобы отточить ошибки' +
              f'из группы {random_mistake.type.name}' if by_group else ''
              f'\nПример ошибки: {random_mistake.user_message}. '
              f'Пояснение к ошибке: {random_mistake.explanation}')
    task = await langlearning_openai_service.choose_one_variant(prompt=prompt)
    return dict(
        text=MistakesTexts.train_mistakes_task(task=task.task, choices=task.enumerated_choices),
        reply_markup=MistakesKeyboards.train_mistake_choice(
            choices=task.enumerated_choices,
            mistake_id=random_mistake.id,
            group=by_group,
            dialog_uuid=by_dialog_uuid
        )
    )


@db_connect()
async def send_train_poll(
        user_id: int, bot: Bot,
        by_group: str | None = None,
        by_dialog_uuid: str | None = None,
        *, db: AsyncSession | None = None
) -> Message:
    random_mistake = await MistakesService(db).get_random_mistake(
        user_id=user_id, by_type_key=by_group,
        by_dialog_uuid=by_dialog_uuid
    )
    task = await send_action_while_do_func(
        coroutine=langlearning_openai_service.choose_one_variant(
            user_message=random_mistake.user_message,
            explanation=random_mistake.explanation,
            group=random_mistake.type.name
        ),
        chat_id=user_id,
        bot=bot,
        action='typing'
    )
    return await bot.send_poll(
        chat_id=user_id,
        question=task.task,
        options=list(map(lambda x: x.text, task.choices)),
        explanation=task.explanation,
        correct_option_id=[i for i, choice in enumerate(task.choices) if choice.is_right][0],
        type='quiz',
        reply_markup=BaseKeyboards.create_kb_back(MistakesListCallback().pack()),
        is_anonymous=False
    )


@router.callback_query(TrainMistakeGroupCallback.filter())
@db_connect()
async def train_mistake_group(
    call: CallbackQuery, callback_data: TrainMistakeGroupCallback,
    state: FSMContext, *,
    db: AsyncSession
):
    if not await UsersService(db).do_paid_action(user_tid=call.from_user.id, credits=1):
        await call.message.answer(
            BaseTexts.CREDITS_OVER,
            reply_markup=CreditsKeyboards.go_to_credits_shop()
        )
        return

    poll_message: Message = await send_train_poll(
        user_id=call.from_user.id,
        bot=call.bot,
        by_group=callback_data.group,
        by_dialog_uuid=callback_data.dialog_uuid,
        db=db
    )
    await state.update_data(
        train_mistakes_group=callback_data.group,
        train_mistakes_dialog=callback_data.dialog_uuid,
        msg_to_del_rm=poll_message.message_id
    )

    # message_data = await create_train_mistake_group(
    #     user_id=call.from_user.id,
    #     by_group=callback_data.group,
    #     by_dialog_uuid=callback_data.dialog_uuid,
    #     db=db
    # )
    # await call.message.answer_poll(
    #     question=
    # )
    # await call.message.answer(**message_data)


@router.poll_answer()
@db_connect()
async def train_mistake_answer(
    poll_answer: PollAnswer,
    state: FSMContext, *,
    db: AsyncSession
):
    if not await UsersService(db).do_paid_action(user_tid=poll_answer.user.id):
        await poll_answer.bot.send_message(
            poll_answer.user.id,
            text=BaseTexts.CREDITS_OVER,
            reply_markup=CreditsKeyboards.go_to_credits_shop()
        )
        return

    data = await state.get_data()
    msg_to_del_rm = data.get('msg_to_del_rm')

    poll_message = await send_train_poll(
        user_id=poll_answer.user.id,
        bot=poll_answer.bot,
        by_group=data.get('train_mistakes_group'),
        by_dialog_uuid=data.get('train_mistakes_dialog'),
        db=db
    )
    await state.update_data(
        msg_to_del_rm=poll_message.message_id
    )
    if msg_to_del_rm:
        try:
            await poll_answer.bot.edit_message_reply_markup(
                message_id=msg_to_del_rm,
                chat_id=poll_answer.user.id,
                reply_markup=None
            )
        except Exception as e:
            print(f'{e=}')


@router.callback_query(TrainMistakeGroupAnswerCallback.filter())
@db_connect()
async def train_mistake_answer(
    call: CallbackQuery,
    callback_data: TrainMistakeGroupAnswerCallback, *,
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

    if not await UsersService(db).do_paid_action(user_tid=call.from_user.id):
        await call.message.edit_text(
            BaseTexts.CREDITS_OVER,
            reply_markup=CreditsKeyboards.go_to_credits_shop()
        )
        return

    await send_train_poll(
        user_id=call.from_user.id,
        bot=call.bot,
        by_group=callback_data.group,
        by_dialog_uuid=callback_data.dialog_uuid,
        db=db
    )