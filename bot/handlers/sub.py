from datetime import timedelta

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, User as TgUser
from database import models
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
    credits_packs = SubsService().get_credits_packs()
    await call.message.edit_text(
        SubsTexts.credits_packs(credits_packs),
        reply_markup=SubsKeyboards.credits_packs(credits_packs)
    )


@router.callback_query(F.data == 'subs')
async def subs(
    call: CallbackQuery
):
    subs = SubsService().get_subs()
    await call.message.edit_text(
        SubsTexts.subs(subs),
        reply_markup=SubsKeyboards.subs(subs)
    )


@router.callback_query(BuyCreditsCallback.filter())
async def buy_credits(
    call: CallbackQuery, callback_data: BuyCreditsCallback
):
    credits_pack = SubsService().get_credits_pack_by_id(callback_data.id)

    await call.message.edit_text(
        SubsTexts.buy_credits_pack(credits_pack),
        reply_markup=SubsKeyboards.test_pay_for_credits(credits_pack.id)
    )


@router.callback_query(BuySubCallback.filter())
async def buy_sub(
    call: CallbackQuery, callback_data: BuySubCallback
):
    sub = SubsService().get_sub(callback_data.id)
    await call.message.edit_text(
        SubsTexts.buy_sub(sub),
        reply_markup=SubsKeyboards.test_pay_for_sub(sub.id)
    )


@router.callback_query(TestBuyCreditsCallback.filter())
async def test_buy_credits(
    call: CallbackQuery, callback_data: TestBuyCreditsCallback,
    db: AsyncSession
):
    await give_credits(
        callback_data.id, user=call.from_user, db=db
    )


@router.callback_query(TestBuySubCallback.filter())
async def test_buy_sub(
    call: CallbackQuery,
    callback_data: TestBuySubCallback,
    db: AsyncSession
):
    await give_sub(
        callback_data.id, user=call.from_user, db=db
    )


async def give_credits(credits_pack_id: int, user: TgUser, db: AsyncSession):
    credits_pack = SubsService().get_credits_pack_by_id(credits_pack_id)
    user_credits = await UsersService(db).update_user_credits(
        user.id, credits=credits_pack.credits, action='up'
    )
    await PaymentsService(db).save_payment(
        user_tid=user.id, amount=credits_pack.price, type=models.PaymentType.credits,
        bot=user.bot
    )
    await user.bot.send_message(
        user.id,
        text='<b>Вы получили:</b> {} кредитов.\n<b>Ваше текущее количество кредитов:</b> {}'
        .format(credits_pack.credits, user_credits)
    )
    user_db = await UsersService(db).get_user(user.id)
    await user.bot.send_message(
        chat_id=user.id,
        text=BaseTexts.start(user.first_name, user_credits, user_db.sub_end),
        reply_markup=BaseKeyboards.main_menu()
    )


async def give_sub(sub_id: int, user: TgUser, db: AsyncSession):
    sub = SubsService().get_sub(sub_id)
    sub_end = await UsersService(db).give_sub(user_tid=user.id, td=timedelta(days=sub.days))
    await PaymentsService(db).save_payment(
        user_tid=user.id, amount=sub.price, type=models.PaymentType.sub,
        bot=user.bot
    )
    await user.bot.send_message(
        user.id,
        text='<b>Ваша подписка продлена на:</b> {} дней.\n<b>Теперь она закончится:</b> {}'
        .format(sub.days, sub_end.strftime('%H:%M %d.%m.%Y'))
    )
    user_credits = await UsersService(db).get_user_credits(user.id)
    await user.bot.send_message(
        chat_id=user.id,
        text=BaseTexts.start(user.first_name, user_credits, sub_end),
        reply_markup=BaseKeyboards.main_menu()
    )