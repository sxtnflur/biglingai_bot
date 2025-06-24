from services.ai.base import ResChoice
from services.mistakes_service import MistakeSchema


class MistakesTexts:
    GROUPS_IF_HAS_MISTAKES = '''
<b>Здесь хранятся твои ошибки. Чем их больше, тем лучше! Главное не забывай их отрабатывать!</b>
{}
<i>Чтобы посмотреть и отработать ошибки выбери одну из групп:</i>
'''

    GROUPS_IF_NO_MISTAKES = '''
Здесь будут храниться твои ошибки, когда ты их допустишь.
Когда-нибудь ты все равно это сделаешь, тогда и приходи сюда
'''

    MISTAKES_LIST = '''
Выберите ошибку, чтобы разобрать её:
'''

    MISTAKE = '''
<b>Группа:</b> {mistake.type.name}

<b>Контекст:</b> {mistake.user_message}

❌ <s>{mistake.incorrect}</s> → <b>{mistake.correct}</b>
ℹ {mistake.explanation}
📌 <b>Пример:</b> {example}
'''
    SELECT_REASON_DELETE_MISTAKE = '''
<b>Выберите причину удаления:</b>
'''

    TRAIN_MISTAKES_ANSWER_IF_RIGHT = '✅ Правильный ответ'
    TRAIN_MISTAKES_ANSWER_IF_WRONG = '❌ Неправильный ответ. Правильный ответ: {}'

    DELETE_BUTTON = 'Удалить'
    I_WORKED_OUT_MISTAKE_REASON_DELETE_BUTTON = 'Я отработал эту ошибку!'
    ERROR_MISTAKE_REASON_DELETE_BUTTON = 'Ошибка выявлена неправильно!'
    EXIT_BUTTON = 'Выйти'
    WORK_OUT_MISTAKE_BUTTON = 'Отработать ошибки'
    START_NEW_DIALOG = 'Начать новый диалог'

    @staticmethod
    def groups_if_has_mistakes(count_worked_mistakes: int = 0) -> str:
        text = MistakesTexts.GROUPS_IF_HAS_MISTAKES
        return text.format('\nТы отработал уже <code>{}</code> ошибок ✨\n'.format(count_worked_mistakes)
                           if count_worked_mistakes else '')

    @staticmethod
    def mistake(mistake: MistakeSchema) -> str:
        return MistakesTexts.MISTAKE.format(
            mistake=mistake,
            example=' | '.join(list(map(lambda x: '<code>{}</code>'.format(x), mistake.example)))
        )

    @staticmethod
    def train_mistakes_task(task: str, choices: list[ResChoice]):
        return task + '\n\n' + '\n'.join(map(lambda x: '{x.id}️⃣ - {x.text}'.format(x=x), choices))

    @staticmethod
    def train_mistakes_answer_if_wrong(right_answer: str) -> str:
        return MistakesTexts.TRAIN_MISTAKES_ANSWER_IF_WRONG.format(right_answer)