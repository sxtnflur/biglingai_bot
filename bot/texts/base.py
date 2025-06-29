from datetime import datetime, timedelta


def td_to_text(td: timedelta) -> str:
    total_seconds = int(td.total_seconds())
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    if days > 0:
        return f"{days}д {hours}ч"
    if hours > 0:
        return f"{hours}ч {minutes}мин"
    if minutes > 0:
        return f"{minutes}мин {seconds}сек"
    return f"{seconds}сек"


class BaseTexts:
    START = '''
{}

<b>Обучение:</b>
<code>💬 Чаттинг</code> - <i>Общайся с ИИ на английском и получай обратную связь!</i>
<code>🔴 Ошибки</code> - <i>Смотри свои допущенные ошибки и отрабатывай их на заданиях!</i>
<code>📖 Словарь</code> - <i>Тренируй словарный запас!</i>
<code>🔄 Переводчик</code> - <i>Переводи с ИИ!</i>

<b>Дополнительно:</b>
<code>🕝 Подписки</code> - <i>Купи подписку и пользуйся всем функционалом бота!</i>
<code>💰 Реф. программа</code> - <i>Получай кредиты бесплатно за приглашенных друзей!</i>
'''.strip()
    SUB = '<b>Подписка закончится через:</b> <code>{}</code>'

    CREDITS_OVER = 'Похоже у тебя нет подписки, необходимой для этого действия. ' \
                   'Оформи её, чтобы полноценно пользоваться ботом:'
    PAGINATION_LEFT = '◀️'
    PAGINATION_RIGHT = '▶️'
    BACK = '⏪ Назад'
    CHATTING_BUTTON = '💬 Чаттинг'
    DICTIONARY_BUTTON = '📖 Словарь'
    MY_MISTAKES_BUTTON = '🔴 Ошибки'
    TRANSLATOR_BUTTON = '🔄 Переводчик'
    SUBS_BUTTON = '🕝 Подписки'
    REF_BUTTON = '💰 Реф. программа'
    MAIN_MENU_BUTTON = '▶ В главное меню'

    @staticmethod
    def start(first_name: str, credits: int = 0, td_before_sub_end: timedelta | None = None):
        return BaseTexts.START.format(
            '\n\n' + (
            BaseTexts.SUB.format(td_to_text(td_before_sub_end))
            if td_before_sub_end and td_before_sub_end > timedelta(seconds=0) else '')
        )