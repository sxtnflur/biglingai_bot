from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.callbacks.base import ScrollingCallback
from bot.callbacks.mistakes import MistakesListCallback
from bot.texts.base import BaseTexts
from typing_extensions import Callable, TypeVar

T = TypeVar('T')


class BaseKeyboards:
    @staticmethod
    def main_menu():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=BaseTexts.CHATTING_BUTTON, callback_data='choose_mode:chatting'),
             InlineKeyboardButton(text=BaseTexts.DICTIONARY_BUTTON, callback_data='dictionary')],
            [InlineKeyboardButton(text=BaseTexts.MY_MISTAKES_BUTTON, callback_data=MistakesListCallback().pack()),
             InlineKeyboardButton(text=BaseTexts.TRANSLATOR_BUTTON, callback_data='translator')],
            [InlineKeyboardButton(text=BaseTexts.SUBS_BUTTON, callback_data='subs'),
            InlineKeyboardButton(text=BaseTexts.REF_BUTTON, callback_data='ref')]
        ])

    @staticmethod
    def create_list_kb(
            objs: list[T], get_btn: Callable[[T], InlineKeyboardButton], width: int = 2
    ) -> list[list[InlineKeyboardButton]]:
        inl_kb = [[]]
        for obj in objs:
            btn = get_btn(obj)
            if len(inl_kb[-1]) >= width:
                inl_kb.append([btn])
            else:
                inl_kb[-1].append(btn)
        return inl_kb

    @staticmethod
    def create_scrolling_kb(
        page: int,
        limit: int,
        callback_data: type[ScrollingCallback],
        objs: list[T],
        get_btn: Callable[[T], InlineKeyboardButton],
        width: int = 2,
        additional_btns: list[list[InlineKeyboardButton]] | None = None,
        pag_btn_additional_kwargs: dict | None = None
    ) -> InlineKeyboardMarkup:
        inl_kb = BaseKeyboards.create_list_kb(objs, get_btn, width)
        pag_btns = []
        if page > 0:
            if pag_btn_additional_kwargs:
                pag_btns.append(InlineKeyboardButton(
                    text=BaseTexts.PAGINATION_LEFT,
                    callback_data=callback_data(page=page-1, limit=limit, **pag_btn_additional_kwargs).pack()
                ))
            else:
                pag_btns.append(InlineKeyboardButton(
                    text=BaseTexts.PAGINATION_LEFT, callback_data=callback_data(page=page-1, limit=limit).pack()
                ))
        if len(objs) == limit:
            if pag_btn_additional_kwargs:
                pag_btns.append(InlineKeyboardButton(
                    text=BaseTexts.PAGINATION_RIGHT,
                    callback_data=callback_data(page=page + 1, limit=limit, **pag_btn_additional_kwargs).pack()
                ))
            else:
                pag_btns.append(InlineKeyboardButton(
                    text=BaseTexts.PAGINATION_RIGHT, callback_data=callback_data(page=page+1, limit=limit).pack()
                ))
        if additional_btns:
            inl_kb += additional_btns

        return InlineKeyboardMarkup(inline_keyboard=inl_kb)

    @staticmethod
    def create_btn_back(callback_data: str):
        return InlineKeyboardButton(text=BaseTexts.BACK, callback_data=callback_data)

    @staticmethod
    def create_kb_back(callback_data: str):
        return InlineKeyboardMarkup(inline_keyboard=[[BaseKeyboards.create_btn_back(callback_data)]])

    @staticmethod
    def to_main_menu():
        return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(
            text=BaseTexts.MAIN_MENU_BUTTON, callback_data='start'
        )]])

    @staticmethod
    def to_subs():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=BaseTexts.SUBS_BUTTON2, callback_data='subs'
            )]
        ])