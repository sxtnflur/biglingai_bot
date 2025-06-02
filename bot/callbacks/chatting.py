from aiogram.filters.callback_data import CallbackData


class SelectChattingTypeCallback(CallbackData, prefix='select-chatting-type'):
    type: str