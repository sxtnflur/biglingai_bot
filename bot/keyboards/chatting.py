from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from bot.texts.base import BaseTexts
from enums import ChattingMessageType
from schemas.chatting import DialogType
from ..callbacks.chatting import SelectChattingTypeCallback, ChangeChattingMessageTypeCallback
from ..texts.chatting import ChattingTexts


class ChattingKeyboards:
    @staticmethod
    def start(current_message_type: ChattingMessageType):
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=ChattingTexts.CHOOSE_DIALOG_MODE, callback_data='chatting_choose_mode')],
            [InlineKeyboardButton(text=ChattingTexts.dialog_message_type_button(current_message_type),
                                  callback_data=ChangeChattingMessageTypeCallback(type=current_message_type.value).pack())],
            [InlineKeyboardButton(text=BaseTexts.BACK, callback_data='start')]
        ])

    @staticmethod
    def ai_answer():
        return ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text=ChattingTexts.END_BUTTON)]
        ], resize_keyboard=True)

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
                text=BaseTexts.BACK, callback_data='choose_mode:chatting'
            )]
        ])