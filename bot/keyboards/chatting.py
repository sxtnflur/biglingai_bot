from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.texts.base import BaseTexts
from schemas.chatting import DialogType
from ..callbacks.chatting import SelectChattingTypeCallback
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

    @staticmethod
    def select_chatting_type():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=ChattingTexts.dialog_type_label(DialogType.SMALL_TALK),
                callback_data=SelectChattingTypeCallback(type=DialogType.SMALL_TALK).pack()
            ),
            InlineKeyboardButton(
                text=ChattingTexts.dialog_type_label(DialogType.LONG_TALK),
                callback_data=SelectChattingTypeCallback(type=DialogType.LONG_TALK).pack()
            )],
            [InlineKeyboardButton(
                text=ChattingTexts.dialog_type_label(DialogType.ROLE_PLAY),
                callback_data=SelectChattingTypeCallback(type=DialogType.ROLE_PLAY).pack()
            ),
            InlineKeyboardButton(
                text=ChattingTexts.dialog_type_label(DialogType.DEBATE),
                callback_data=SelectChattingTypeCallback(type=DialogType.DEBATE).pack()
            )],
            [InlineKeyboardButton(
                text=ChattingTexts.dialog_type_label(DialogType.STORY),
                callback_data=SelectChattingTypeCallback(type=DialogType.STORY).pack()
            ),
            InlineKeyboardButton(
                text=ChattingTexts.dialog_type_label(DialogType.CULTURE),
                callback_data=SelectChattingTypeCallback(type=DialogType.CULTURE).pack()
            )],
            [InlineKeyboardButton(
                text=ChattingTexts.dialog_type_label(DialogType.NEWS),
                callback_data=SelectChattingTypeCallback(type=DialogType.NEWS).pack()
            )],
            [InlineKeyboardButton(
                text=BaseTexts.BACK, callback_data='start'
            )]
        ])