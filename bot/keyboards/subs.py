from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.callbacks.subs import BuyCreditsCallback, BuySubCallback, TestBuyCreditsCallback, TestBuySubCallback
from bot.keyboards.base import BaseKeyboards
from schemas.subs import CreditsPack, Sub
from typing_extensions import Literal


class SubsKeyboards:

    @staticmethod
    def credits_or_subs():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text='Кредиты', callback_data='credits'
            ), InlineKeyboardButton(
                text='Подписки', callback_data='subs'
            )],
            [InlineKeyboardButton(
                text='Назад', callback_data='start'
            )]
        ])

    @staticmethod
    def credits_packs(credits: list[CreditsPack]):
        inl_kb = BaseKeyboards.create_list_kb(
            objs=credits,
            get_btn=lambda credit: InlineKeyboardButton(
                text='{} кредитов'.format(credit.credits),
                callback_data=BuyCreditsCallback(id=credit.id).pack()
            ),
            width=1
        )
        return InlineKeyboardMarkup(inline_keyboard=inl_kb + [[InlineKeyboardButton(
            text='Назад', callback_data='credits_subs'
        )]])

    @staticmethod
    def subs(subs: list[Sub]):
        inl_kb = BaseKeyboards.create_list_kb(
            objs=subs,
            get_btn=lambda sub: InlineKeyboardButton(
                text='{} дней'.format(sub.days),
                callback_data=BuySubCallback(id=sub.id).pack()
            ),
            width=1
        )
        return InlineKeyboardMarkup(inline_keyboard=inl_kb + [[InlineKeyboardButton(
            text='Назад', callback_data='credits_subs'
        )]])


    @staticmethod
    def pay(pay_url: str, credits_or_subs: Literal['credits', 'subs']):
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text='Оплата', callback_data='-'
            )],
            [InlineKeyboardButton(
                text='Назад', callback_data='credits' if credits_or_subs == 'credits' else 'subs'
            )]
        ])

    @staticmethod
    def test_pay_for_sub(sub_id: int):
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text='Оплата', callback_data=TestBuySubCallback(id=sub_id).pack()
            )],
            [InlineKeyboardButton(
                text='Назад', callback_data='subs'
            )]
        ])

    @staticmethod
    def test_pay_for_credits(credits_pack_id: int):
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text='Оплата', callback_data=TestBuyCreditsCallback(id=credits_pack_id).pack()
            )],
            [InlineKeyboardButton(
                text='Назад', callback_data='credits'
            )]
        ])