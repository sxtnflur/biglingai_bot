from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from ..texts.base import BaseTexts
from ..texts.subs import SubsTexts


class CreditsKeyboards:
    @staticmethod
    def go_to_credits_shop():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=SubsTexts.I_WANT_MORE_BUTTON,
                callback_data='subs'
            )],
            [InlineKeyboardButton(
                text=BaseTexts.BACK,
                callback_data='start'
            )]
        ])