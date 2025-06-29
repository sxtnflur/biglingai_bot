from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.callbacks.dictionary import AddWordToDictCallback
from bot.texts.base import BaseTexts


class TranslatorKeyboards:
    @staticmethod
    def translated_text(en_text: str):
        inl_kb = []
        if len(en_text.split()) == 1:
            inl_kb.insert(0, [InlineKeyboardButton(
                text='📖 Добавить в словарь',
                callback_data=AddWordToDictCallback(word=en_text).pack()
            )])
        inl_kb.append([InlineKeyboardButton(
            text=BaseTexts.MAIN_MENU_BUTTON, callback_data='start'
        )])
        return InlineKeyboardMarkup(inline_keyboard=inl_kb)