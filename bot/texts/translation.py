from services.translator import TranslationResult


class TranslationTexts:
    MAIN = '''
❗ <b>Заходить в этот раздел необязательно</b> ❗
ℹ <i>Ты можешь отправить текст в любом разделе бота и я его переведу</i>

<i>Попробуй прямо сейчас, введи любой текст на русском или английском:</i>
'''

    @staticmethod
    def show_translation(translation_result: TranslationResult):
        text = '''    
<b>Ваш текст ({}):</b>
<blockquote>{}</blockquote>
---------------------------
<b>Перевод ({}):</b>
<blockquote>{}</blockquote>
'''.format(translation_result.orig_language.upper(), translation_result.orig,
           translation_result.translated_language.upper(), translation_result.translated).strip()
        if len(translation_result.en_text.split()) == 1:
            text += '\n\n<i>Добавить слово "{}" в словарь?</i>'.format(translation_result.en_text)
        return text