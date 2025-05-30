from datetime import datetime


class BaseTexts:
    START = '''
Привет, {}! Рад тебя видеть! Готов изучать английский?

У тебя есть <b>{}</b> кредитов{}

Выбери режим!
'''.strip()
    SUB = '<b>Подписка закончится:</b> {}'

    CREDITS_OVER = 'У тебя не хватает кредитов. Пополни их, чтобы продолжить'

    @staticmethod
    def start(first_name: str, credits: int = 0, sub_end: datetime | None = None):
        return BaseTexts.START.format(first_name, credits,
            '\n' + BaseTexts.SUB.format(sub_end.strftime('%H:%M %d.%m.%Y')) if sub_end else ''
        )