from aiogram.filters.callback_data import CallbackData
from .base import ScrollingCallback

class AddWordToDictCallback(CallbackData, prefix='add-word-to-dict'):
    word: str


class MarkDictWordAsWorkedCallback(CallbackData, prefix='mark-dict-word-as-worked'):
    word_id: int
    from_training: bool = True


class DictWordsListCallback(ScrollingCallback, prefix='dict-words-list'):
    order_by: str = 'alphabet'
    order_asc: bool = True
    change_order: bool = False