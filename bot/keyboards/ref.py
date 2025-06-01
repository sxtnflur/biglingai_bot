from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from ..texts.ref import RefTexts
from ..texts.base import BaseTexts


class RefKeyboards:
    @staticmethod
    def main(is_special: bool):
        inl_kb = []
        if is_special:
            inl_kb.append([InlineKeyboardButton(
                text=RefTexts.SPECIAL_REF_BUTTON, callback_data='about-special-ref'
            )])
        return InlineKeyboardMarkup(inline_keyboard=inl_kb + [[InlineKeyboardButton(
            text=BaseTexts.BACK, callback_data='start'
        )]])

    @staticmethod
    def on_ref_event():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=RefTexts.ALL_STATISTIC_BUTTON, callback_data='ref'
            )],
            [InlineKeyboardButton(
                text=RefTexts.DELETE_THIS_MESSAGE, callback_data='delete-this-message'
            )]
        ])

    @staticmethod
    def about_special_ref(on_moderation: bool = False):
        inl_kb = [] if on_moderation else [[InlineKeyboardButton(
                text=RefTexts.SEND_ORDER_SPECIAL_REF_BUTTON, callback_data='special-ref-submit-request'
            )]]
        inl_kb.append([
            InlineKeyboardButton(
                text=BaseTexts.BACK, callback_data='ref'
            )
        ])
        return InlineKeyboardMarkup(inline_keyboard=inl_kb)