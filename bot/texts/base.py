from datetime import datetime, timedelta

from config import settings


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
    START = f'''
<b>Обучение:</b>
<tg-emoji emoji-id="5443038326535759644">💬</tg-emoji> <a href="{settings.BOT_URL}?start=screen-chatting">Чаттинг</a> - <i>Общайся с ИИ на английском и получай обратную связь!</i>
<tg-emoji emoji-id="5420323339723881652">⚠</tg-emoji> <a href="{settings.BOT_URL}?start=screen-mistakes">Ошибки</a> - <i>Смотри свои допущенные ошибки и отрабатывай их на заданиях!</i>
<a href="{settings.BOT_URL}?start=screen-dictionary">📖 Словарь</a> - <i>Тренируй словарный запас!</i>
<a href="{settings.BOT_URL}?start=screen-translator">🔄 Переводчик</a> - <i>Переводи с ИИ!</i>

<b>Дополнительно:</b>
<tg-emoji emoji-id="5413879192267805083">🗓</tg-emoji> <a href="{settings.BOT_URL}?start=screen-sub">Подписки</a> - <i>Купи подписку и пользуйся всем функционалом бота!</i>
<tg-emoji emoji-id="5229064374403998351">🛍</tg-emoji> <a href="{settings.BOT_URL}?start=screen-ref">Реф. программа</a> - <i>Получи подписку бесплатно за приглашенных друзей!</i>
'''.strip()
    SUB = '<b>Подписка закончится через:</b> <code>{}</code>'

    CREDITS_OVER = 'Похоже у тебя нет подписки, необходимой для этого действия. ' \
                   'Оформи её, чтобы полноценно пользоваться ботом:'
    PAGINATION_LEFT = '◀️'
    PAGINATION_RIGHT = '▶️'
    BACK = '⏪ Назад'
    CHATTING_BUTTON = '💬 Чаттинг'
    DICTIONARY_BUTTON = '📖 Словарь'
    MY_MISTAKES_BUTTON = '⚠ Ошибки'
    TRANSLATOR_BUTTON = '🔄 Переводчик'
    SUBS_BUTTON = '🗓 Подписки'
    REF_BUTTON = '💰 Реф. программа'
    MAIN_MENU_BUTTON = '▶ В главное меню'

    SUBS_BUTTON2 = 'К подпискам'

    @staticmethod
    def start(*args, **kwargs):
        return BaseTexts.START