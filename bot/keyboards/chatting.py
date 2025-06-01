from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.texts.base import BaseTexts
from ..texts.chatting import ChattingTexts


class ChattingKeyboards:
    @staticmethod
    def start():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=ChattingTexts.START_BUTTON, callback_data='chatting_mode_start')],
            [InlineKeyboardButton(text=BaseTexts.BACK, callback_data='start')]
        ])

    @staticmethod
    def ai_answer():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=ChattingTexts.END_BUTTON, callback_data='start')]
        ])