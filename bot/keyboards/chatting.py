from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


class ChattingKeyboards:

    @staticmethod
    def start():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Начали!', callback_data='chatting_mode_start')],
            [InlineKeyboardButton(text='Назад', callback_data='start')]
        ])

    @staticmethod
    def ai_answer():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Закончить предварительно', callback_data='start')]
        ])