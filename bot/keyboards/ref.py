from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, SwitchInlineQueryChosenChat, CopyTextButton
from ..texts.ref import RefTexts
from ..texts.base import BaseTexts


class RefKeyboards:
    @staticmethod
    def main(is_special: bool, ref_link: str):
        inl_kb = [[InlineKeyboardButton(
                text='Пригласить друга',
                switch_inline_query_chosen_chat=SwitchInlineQueryChosenChat(
                    query='Приходи в бота изучать английский по ссылке!\n{}'.format(ref_link),
                    allow_user_chats=True,
                    allow_bot_chats=False,
                    allow_group_chats=True,
                    allow_channel_chats=True
                )
            ), InlineKeyboardButton(
            text='Скопировать ссылку',
            copy_text=CopyTextButton(text=ref_link)
        )]]
        if not is_special:
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