from aiogram.filters.callback_data import CallbackData


class AddWordToDictCallback(CallbackData, prefix='add-word-to-dict'):
    word: str


class MarkDictWordAsWorkedCallback(CallbackData, prefix='mark-dict-word-as-worked'):
    word_id: int
    from_training: bool = True