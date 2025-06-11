from datetime import datetime


class BaseTexts:
    START = '''
Привет, {}! Готов изучать английский?

{}

<b>Обучение:</b>
<code>✏ Чаттинг</code> - <i>Общайся с ИИ текстом на английском и получай обратную связь</i>
<code>🔴 Ошибки</code> - <i>Смотри свои допущенные ошибки и отрабатывай их на заданиях</i>
<code>🔄 Переводчик</code> - <i>Переводи с ИИ: ru -> en и en -> ru</i>

<b>Дополнительно:</b>
<code>🕝 Подписки</code> - <i>Купи подписку и пользуйся всеми  ботом</i>
<code>💰 Реф. программа</code> - <i>Получай кредиты бесплатно за приглашенных друзей</i>
'''.strip()
    SUB = '<b>Подписка закончится:</b> <code>{}</code>'

    CREDITS_OVER = 'У тебя не хватает кредитов. Пополни их, чтобы продолжить'
    PAGINATION_LEFT = '◀️'
    PAGINATION_RIGHT = '▶️'
    BACK = '⏪ Назад'
    CHATTING_BUTTON = '✏ Чаттинг'
    MY_MISTAKES_BUTTON = '🔴 Ошибки'
    TRANSLATOR_BUTTON = '🔄 Переводчик'
    SUBS_BUTTON = '🕝 Подписки'
    REF_BUTTON = '💰 Реф. программа'

    @staticmethod
    def start(first_name: str, credits: int = 0, sub_end: datetime | None = None):
        return BaseTexts.START.format(first_name,
            '\n' + BaseTexts.SUB.format(sub_end.strftime('%H:%M %d.%m.%Y')) if sub_end else ''
        )