from services.translator import TranslationResult


class TranslationTexts:
    MAIN = '''
Это переводчик с русского на английский и с английского на русский

ℹ <i>Вы можете отправить текст в любом разделе бота и нажать "Перевести"</i>

Введи текст и получи перевод:
'''

    @staticmethod
    def show_translation(translation_result: TranslationResult):
        return '''    
<b>Ваш текст ({}):</b>
<blockquote>{}</blockquote>
---------------------------
<b>Перевод ({}):</b>
<blockquote>{}</blockquote>
'''.format(translation_result.orig_language.upper(), translation_result.orig,
           translation_result.translated_language.upper(), translation_result.translated)