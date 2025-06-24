from datetime import datetime


class BaseTexts:
    START = '''
Привет, {}! Готов изучать английский?

{}{}

<b>Обучение:</b>
<code>✏ Чаттинг</code> - <i>Общайся с ИИ текстом на английском и получай обратную связь</i>
<code>🔴 Ошибки</code> - <i>Смотри свои допущенные ошибки и отрабатывай их на заданиях</i>
<code>🔄 Переводчик</code> - <i>Переводи с ИИ</i>

<b>Дополнительно:</b>
<code>🕝 Подписки</code> - <i>Купи подписку и пользуйся всем функционалом бота</i>
<code>💰 Реф. программа</code> - <i>Получай кредиты бесплатно за приглашенных друзей</i>
'''.strip()
    SUB = '<b>Подписка закончится:</b> <code>{}</code>'

    CREDITS_OVER = 'Похоже у тебя нет подписки, необходимой для этого действия. ' \
                   'Оформи её, чтобы полноценно пользоваться ботом:'
    PAGINATION_LEFT = '◀️'
    PAGINATION_RIGHT = '▶️'
    BACK = '⏪ Назад'
    CHATTING_BUTTON = '✏ Чаттинг'
    DICTIONARY_BUTTON = '📖 Словарь'
    MY_MISTAKES_BUTTON = '🔴 Ошибки'
    TRANSLATOR_BUTTON = '🔄 Переводчик'
    SUBS_BUTTON = '🕝 Подписки'
    REF_BUTTON = '💰 Реф. программа'

    @staticmethod
    def start(first_name: str, credits: int = 0, sub_end: datetime | None = None):
        return BaseTexts.START.format(
            first_name,
            '\nТебе доступно <code>{}</code> бесплатных использований.\n'
            '<i>(-1 за каждое сообщение в чаттинге/задание в ошибках/генерацию в переводчике и т.д.)</i>'
            .format(credits) if credits else '',
            '\n' + (
            BaseTexts.SUB.format(sub_end.strftime('%H:%M %d.%m.%Y'))
            if sub_end and sub_end > datetime.utcnow() else '')
        )