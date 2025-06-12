

class TranslationTexts:
    MAIN = '''
Это переводчик с русского на английский и с английского на русский

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