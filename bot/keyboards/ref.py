from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


class RefKeyboards:

    @staticmethod
    def main(is_special: bool):
        inl_kb = []
        if is_special:
            inl_kb.append([InlineKeyboardButton(
                text='Специальная программа', callback_data='about-special-ref'
            )])
        return InlineKeyboardMarkup(inline_keyboard=inl_kb + [[InlineKeyboardButton(
            text='В главное меню', callback_data='start'
        )]])

    @staticmethod
    def on_ref_event():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text='📊 Смотреть всю статистику', callback_data='ref'
            )],
            [InlineKeyboardButton(
                text='🗑 Удалить это сообщение', callback_data='delete-this-message'
            )]
        ])

    @staticmethod
    def about_special_ref(on_moderation: bool = False):
        inl_kb = [] if on_moderation else [[InlineKeyboardButton(
                text='Подать заявку', callback_data='special-ref-submit-request'
            )]]
        inl_kb.append([
            InlineKeyboardButton(
                text='Назад', callback_data='ref'
            )
        ])
        return InlineKeyboardMarkup(inline_keyboard=inl_kb)