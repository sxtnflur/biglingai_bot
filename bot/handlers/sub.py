from datetime import timedelta

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, User as TgUser
from depends import payment_factory, subs_service, payments_service, scheduler
from services.payments_service import PaymentsService
from services.users_service import UsersService
from sqlalchemy.ext.asyncio import AsyncSession
from ..callbacks.subs import BuyCreditsCallback, BuySubCallback, TestBuyCreditsCallback, TestBuySubCallback
from ..keyboards.base import BaseKeyboards
from ..middlewares import DatabaseMiddleware
from ..texts.base import BaseTexts
from ..texts.subs import SubsTexts
from ..keyboards.subs import SubsKeyboards
from services.subs_service import SubsService

router = Router()
router.callback_query.middleware(DatabaseMiddleware())


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


@router.callback_query(F.data == 'subs')
async def subs(
    call: CallbackQuery, db: AsyncSession
):
    subs = await subs_service.get_subs(db=db)
    user = await UsersService(db).get_user(call.from_user.id)
    await call.message.edit_text(
        SubsTexts.subs(
            subs,
            has_autopayment=user.is_autopayment,
            td_before_sub_end=user.td_before_sub_end,
            current_sub=user.cu
        ),
        reply_markup=SubsKeyboards.subs(subs, has_autopayment=user.is_autopayment)
    )


# @router.callback_query(BuyCreditsCallback.filter())
# async def buy_credits(
#     call: CallbackQuery, callback_data: BuyCreditsCallback, db: AsyncSession
# ):
#     credits_pack = SubsService().get_credits_pack_by_id(callback_data.id)
#     pay_data = await payment_factory.create_payment(
#         payment_method='yookassa',
#         amount=credits_pack.price,
#         description='Покупка {} кредитов'.format(credits_pack.credits)
#     )
#     await PaymentsService(db).save_payment(
#         user_tid=call.from_user.id,
#         amount=credits_pack.price,
#         type=PaymentType.credits,
#         order_id=pay_data.id
#     )
#     await call.message.edit_text(
#         SubsTexts.buy_credits_pack(credits_pack),
#         reply_markup=SubsKeyboards.pay(pay_data.url, 'credits')
#     )


@router.callback_query(BuySubCallback.filter())
async def buy_sub(
    call: CallbackQuery, callback_data: BuySubCallback, db: AsyncSession
):
    sub = await subs_service.get_sub(callback_data.id, db=db)
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
async def cancel_autopayment(
    call: CallbackQuery, db: AsyncSession
):
    await subs_service.cancel_autopayment(
        user_id=call.from_user.id, db=db
    )
    scheduler.autopayment_scheduler.remove_user_job(call.from_user.id)
    await call.answer('Автопродление подписки отменено', show_alert=True)
    await subs(call, db)


# @router.callback_query(F.data == 'return-autopayment')
# async def return_autopayment(
#     call: CallbackQuery, db: AsyncSession
# ):
#     await subs_service.return_autopayment_to_user(
#         user_id=call.from_user.id, db=db
#     )