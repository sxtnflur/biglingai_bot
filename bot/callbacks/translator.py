from aiogram.filters.callback_data import CallbackData


class TranslateWordCallback(CallbackData, prefix='translate-word'):
    word: str


class TranslateThisPhraseCallback(CallbackData, prefix='translate-this-phrase'):
    from_index: int
    to_index: int