from schemas.dictionary import DictionaryWord, UserDictionaryWord


class DictionaryTexts:
    MAIN = '''
{}

Пополняй свой словарь словами и тренируйся на них

<code>👁️</code> - <i>Посмотри свои слова в словаре</i>
<code>➕</code> - <i>Узнай все способы добавить слово в словарь</i>
<code>🕹️ Тренировка</code> - <i>Тренируй и пополняй свой словарный запас</i>
'''
    HOW_TO_ADD_WORD_INSTRUCTION = '''
❗ <b>Заходить в этот раздел необязательно</b> ❗
ℹ <i>Ты можешь отправить ОДНО СЛОВО в любом разделе бота, а после нажать кнопку "Добавить в словарь"</i>

<i>Попробуй прямо сейчас, введи любое ОДНО слово на русском или английском:</i>
'''.strip()

    @staticmethod
    def main(
            count_total_worked_words: int,
            count_worked_in_bot_words: int,
            count_already_know_words: int
    ):
        return DictionaryTexts.MAIN.format(
            '''Ты знаешь как минимум <b>{}</b> слов:
    - <b>{}</b> узнал в боте
    - <b>{}</b> знал изначально'''.format(count_total_worked_words, count_worked_in_bot_words, count_already_know_words)
            if count_total_worked_words else ''
        )

    @staticmethod
    def select_right_translation(word: str):
        return '<b>Выбери правильный вариант перевода для слова</b>\n\n<i>{}</i>'.format(word.capitalize())

    @staticmethod
    def what_do_with_your_text(text: str):
        return '<b>Что вы хотите сделать {}❓</b>\n<blockquote>{}</blockquote>'.format(
            'с этим словом' if len(text.split()) == 1 else 'с этой фразой', text.strip())

    @staticmethod
    def word_is_added_to_dict(word_data: DictionaryWord):
        return '''
✅ <b>Слово добавлено в словарь!</b>

"{en_word}" ➡  {ru_words}
'''.format(ru_words=', '.join(list(map(lambda x: f'"{x}"', word_data.ru_words))),
           en_word=word_data.word.capitalize())

    @staticmethod
    def word_remember_card(word_data: DictionaryWord):
        return '''
ℹ <b>Постарайся запомнить перевод слова:</b>
<i>Перед нажатием на перевод слова попробуй подумать над ним самостоятельно!</i>

<blockquote>{}</blockquote>

<b>Перевод:</b> <span class="tg-spoiler">{}</span>
'''.format(word_data.word, ', '.join(word_data.ru_words))

    @staticmethod
    def word_remember_task(word: str):
        return '✍ <b>Введи перевод слова:</b>\n<blockquote>{word}</blockquote>'.format(word=word)

    @staticmethod
    def train_word_success(ru_words: list[str]):
        return '✅ <b>Все верно! Перевод:</b> <blockquote>{}</blockquote>'.format(', '.join(ru_words))

    @staticmethod
    def train_word_wrong(ru_words: list[str]):
        return '❌ <b>Увы, неверно! Правильный перевод:</b> <blockquote>{}</blockquote>'.format(', '.join(ru_words))

    @staticmethod
    def word_can_be_marked_as_worked(word: str):
        return '👏 Похоже, вы запомнили слово <blockquote>{}</blockquote>\n\nПереместим его в "Отработанные"?'.format(
            word)

    @staticmethod
    def dict_words_list(user_words: list[UserDictionaryWord]):
        def get_level_circle(learning_rate: int, can_be_worked: bool):
            if can_be_worked:
                return '🟢'
            if learning_rate <= 1:
                return '🔴'
            elif learning_rate <= 5:
                return '🟠'
            elif learning_rate < 10:
                return '🟡'
            else:
                return '🟢'

        for uw in user_words:
            print(f'{uw.learning_rate=}')

        words_texts = '\n'.join([
            f'• <code>{uw.word.word}</code> ➡ {", ".join(list(map(lambda x: f"<code>{x}</code>", uw.word.ru_words)))} ' \
            f'{get_level_circle(uw.learning_rate, uw.can_be_mark_as_worked)}'.ljust(33)
            for uw in user_words
        ])
        return '''
<i>🔴 - Только начал запоминать
🟠 - Смог перевести несколько раз
🟡 - Почти запомнил
🟢 - Знаю</i>

{}        
'''.format(words_texts)
