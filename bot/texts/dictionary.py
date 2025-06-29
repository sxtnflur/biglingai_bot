from schemas.dictionary import DictionaryWord, UserDictionaryWord


class DictionaryTexts:
    MAIN = '''
<b>Это словарь</b>

Пополняй свой словарь словами и тренируйся на них

<code>👁️</code> - <i>Посмотри свои слова в словаре</i>
<code>➕</code> - <i>Узнай все способы добавить слово в словарь</i>
<code>🕹️ Тренировка</code> - <i>Тренируй свой словарный запас по своему словарю</i>
'''
    HOW_TO_ADD_WORD_INSTRUCTION = '''
<b>Есть несколько способов добавить слово в словарь:</b>

<b>1.</b> Отправить этому боту слово и выбрать "Добавить в словарь"
<b>2.</b> Переслать сообщение с одним словом и выбрать "Добавить в словарь"
<b>3.</b> Переслать сообщение с одним словом и написать "В словарь"
<b>4.</b> В разделе <code>[📖 Словарь -> 🔁 Тренировка]</code> если у тебя нет своих слов или они закончились, 
мы добавим тебе свое
'''


    @staticmethod
    def what_do_with_your_text(text: str):
        return '<b>Что вы хотите сделать {}❓</b>\n<blockquote>{}</blockquote>'.format(
            'с этим словом' if len(text.split()) == 1 else 'с этой фразой', text.strip())

    @staticmethod
    def word_is_added_to_dict(word_data: DictionaryWord):
        return '''
✅ <b>Слово добавлено в словарь!</b>

{ru_word} ➡ {en_word}
'''.format(ru_word=word_data.ru_word.capitalize(),
           en_word=word_data.word.capitalize())

    @staticmethod
    def word_remember_card(word_data: DictionaryWord):
        return '''
ℹ <b>Постарайся запомнить перевод слова:</b>
<i>Перед нажатием на перевод слова попробуй подумать над ним самостоятельно!</i>

<blockquote>{}</blockquote>

<b>Перевод:</b> <span class="tg-spoiler">{}</span>
'''.format(word_data.word, word_data.ru_word)

    @staticmethod
    def word_remember_task(word: str):
        return '✍ <b>Введи перевод слова:</b>\n<blockquote>{word}</blockquote>'.format(word=word)

    @staticmethod
    def train_word_success(ru_word: str):
        return '✅ <b>Все верно! Перевод:</b> <blockquote>{}</blockquote>'.format(ru_word)

    @staticmethod
    def train_word_wrong(ru_word: str):
        return '❌ <b>Увы, неверно! Правильный перевод:</b> <blockquote>{}</blockquote>'.format(ru_word)

    @staticmethod
    def word_can_be_marked_as_worked(word: str):
        return '👏 Похоже, вы запомнили слово <blockquote>{}</blockquote>\n\nПереместим его в "Отработанные"?'.format(word)

    @staticmethod
    def dict_words_list(user_words: list[UserDictionaryWord]):
        def get_level_circle(learning_rate: int, can_be_worked: bool):
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
            f'• <code>{uw.word.word}</code>    ➡    <code>{uw.word.ru_word}</code> ' \
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
