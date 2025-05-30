from aiogram.filters.callback_data import CallbackData


class BuyCreditsCallback(CallbackData, prefix='buy-credits'):
    id: int


class BuySubCallback(CallbackData, prefix='buy-sub'):
    id: int


class TestBuyCreditsCallback(CallbackData, prefix='test-buy-credits'):
    id: int


class TestBuySubCallback(CallbackData, prefix='test-buy-sub'):
    id: int