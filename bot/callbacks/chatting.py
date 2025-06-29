from aiogram.filters.callback_data import CallbackData


class SelectChattingTypeCallback(CallbackData, prefix='select-chatting-type'):
    type: str


class ChangeChattingMessageTypeCallback(CallbackData, prefix='change-chatting-message-type'):
    type: int