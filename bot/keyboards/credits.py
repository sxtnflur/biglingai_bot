from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


class CreditsKeyboards:
    @staticmethod
    def go_to_credits_shop():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text='Хочу еще!',
                callback_data='credits_subs'
            )],
            [InlineKeyboardButton(
                text='В главное меню',
                callback_data='start'
            )]
        ])