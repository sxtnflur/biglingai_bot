

class TranslationTexts:
    MAIN = '''
Это переводчик с русского на английский и с английского на русский

ℹ <i>Вы можете отправить текст в любом разделе бота и нажать "Перевести"</i>

Введи текст и получи перевод:
'''

    @staticmethod
    def show_translation(orig_word: str, translated_word: str):
        return '''    
<b>Ваш текст:</b>
<blockquote>{}</blockquote>
---------------------------
<b>Перевод:</b>
<blockquote>{}</blockquote>
'''.format(orig_word, translated_word)