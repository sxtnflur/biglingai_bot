from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.callbacks.dictionary import AddWordToDictCallback, MarkDictWordAsWorkedCallback
from bot.callbacks.translator import TranslateWordCallback, TranslateThisPhraseCallback


class DictionaryKeyboards:
    @staticmethod
    def main():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text='➕ Добавить', callback_data='how-to-add-word-to-dict'
            )],
            [InlineKeyboardButton(
                text='🔁 Тренировка', callback_data='train-my-dict'
            )],
            [InlineKeyboardButton(
                text='⏪ Назад', callback_data='start'
            )]
        ])

    @staticmethod
    def do_action_with_word(word: str, translate_split: tuple[int, int]):
        inl_kb = [
            [InlineKeyboardButton(
                text='🔁 Перевести', callback_data=TranslateThisPhraseCallback(
                    from_index=translate_split[0], to_index=translate_split[1]
                ).pack()
            )],
            [InlineKeyboardButton(
                text='🗑️ Ничего, удали это сообщение!', callback_data='delete-this-message'
            )]
        ]
        print(f'{word=}')
        if len(word.split()) == 1:
            inl_kb.insert(0, [InlineKeyboardButton(
                text='📖 Добавить в словарь', callback_data=AddWordToDictCallback(word=word).pack()
            )])
        return InlineKeyboardMarkup(inline_keyboard=inl_kb)

    @staticmethod
    def train_card():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Следующее ⏩', callback_data='train-my-dict')],
            [InlineKeyboardButton(text='⏪ Выйти', callback_data='dictionary')]
        ])

    @staticmethod
    def word_is_added_to_dict():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='📖 В словарь', callback_data='dictionary')],
            [InlineKeyboardButton(text='⏪ В главное меню', callback_data='start'),
            InlineKeyboardButton(text='🗑️ Удалить это сообщение', callback_data='delete-this-message')]
        ])

    @staticmethod
    def exit():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='⏪ Выйти', callback_data='dictionary')]
        ])

    @staticmethod
    def word_can_be_marked_as_worked(word_id: int):
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='✅ Да!', callback_data=MarkDictWordAsWorkedCallback(word_id=word_id).pack())],
            [InlineKeyboardButton(text='❌ Нет, хочу еще проработать', callback_data='delete-this-message')]
        ])