from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from database.decorator import db_connect
from depends import payment_factory, subs_service, payments_service, scheduler
from services.users_service import UsersService
from sqlalchemy.ext.asyncio import AsyncSession
from ..callbacks.subs import BuySubCallback
from ..texts.subs import SubsTexts
from ..keyboards.subs import SubsKeyboards

router = Router()


@router.callback_query(F.data == 'credits_subs')
async def credits_subs(
    call: CallbackQuery
):
    await call.message.edit_text(
        SubsTexts.CREDITS_AND_SUBS,
        reply_markup=SubsKeyboards.credits_or_subs()
    )


@router.callback_query(F.data == 'credits')
async def credits(
    call: CallbackQuery
):
    credits_packs = subs_service.get_credits_packs()
    await call.message.edit_text(
        SubsTexts.credits_packs(credits_packs),
        reply_markup=SubsKeyboards.credits_packs(credits_packs)
    )


@db_connect()
async def subs_message(
    message: Message, *, db: AsyncSession
):
    subs = await subs_service.get_subs(db=db)
    user = await UsersService(db).get_user_with_sub(message.from_user.id)

    if user.sale_percent:
        for sub in subs:
            if sub.days == 30:
                sub.sale = sub.price
                sub.price = round(sub.price - (sub.price * (user.sale_percent / 100)))

    await message.answer(
        SubsTexts.subs(
            subs,
            has_autopayment=user.is_autopayment,
            td_before_sub_end=user.td_before_sub_end,
            current_sub=user.current_sub
        ),
        reply_markup=SubsKeyboards.subs(subs, has_autopayment=user.is_autopayment)
    )


@router.callback_query(F.data == 'subs')
@db_connect()
async def subs(
    call: CallbackQuery, *, db: AsyncSession
):
    subs = await subs_service.get_subs(db=db)
    user = await UsersService(db).get_user_with_sub(call.from_user.id)

    if user.sale_percent:
        for sub in subs:
            if sub.days == 30:
                sub.sale = sub.price
                sub.price = round(sub.price - (sub.price * (user.sale_percent / 100)))

    await call.message.edit_text(
        SubsTexts.subs(
            subs,
            has_autopayment=user.is_autopayment,
            td_before_sub_end=user.td_before_sub_end,
            current_sub=user.current_sub
        ),
        reply_markup=SubsKeyboards.subs(subs, has_autopayment=user.is_autopayment)
    )


@router.callback_query(BuySubCallback.filter())
@db_connect()
async def buy_sub(
    call: CallbackQuery, callback_data: BuySubCallback, *, db: AsyncSession
):
    sub = await subs_service.get_sub(callback_data.id, db=db)
    if sub.days == 30:
        user = await UsersService(db).get_user(call.from_user.id)
        if user.sale_percent:
            sub.price = round(sub.price - (sub.price * (user.sale_percent / 100)))

    pay_data = await payment_factory.create_payment(
        payment_method='yookassa',
        amount=sub.price,
        description='Покупка подписки'
    )
    await payments_service.save_payment(
        db=db,
        user_tid=call.from_user.id,
        amount=sub.price,
        order_id=pay_data.id,
        sub_id=sub.id
    )
    await call.message.edit_text(
        SubsTexts.buy_sub(sub),
        reply_markup=SubsKeyboards.pay(pay_data.url, 'subs')
    )


@router.callback_query(F.data == 'cancel-autopayment')
async def pre_cancel_autopayment(
    call: CallbackQuery
):
    await call.message.edit_text(
        '❗ Вы уверены, что хотите отменить автопродление подписки? ❗',
        reply_markup=SubsKeyboards.cancel_autopayment()
    )


@router.callback_query(F.data == 'cancel-autopayment-2')
@db_connect()
async def cancel_autopayment(
    call: CallbackQuery, *, db: AsyncSession
):
    await subs_service.cancel_autopayment(
        user_id=call.from_user.id, db=db
    )
    scheduler.autopayment_scheduler.remove_user_job(call.from_user.id)
    await call.answer('Автопродление подписки отменено', show_alert=True)
    await subs(call, db)
