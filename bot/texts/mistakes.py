from services.mistakes_service import MistakeSchema


class MistakesTexts:
    GROUPS_IF_HAS_MISTAKES = '''
Здесь хранятся твои ошибки. Чем их больше, тем лучше!
Главное не забывай их отрабатывать!

Для этого выбери одну из групп       
'''

    GROUPS_IF_NO_MISTAKES = '''
Здесь будут храниться твои ошибки, когда ты их допустишь.
Когда-нибудь ты все равно это сделаешь, тогда и приходи сюда
'''

    MISTAKES_LIST = '''
Выберите ошибку, чтобы разобрать её:    
'''

    MISTAKE = '''
<b>Группа:</b> {mistake.subgroup.subgroup_label}

<b>Контекст:</b> {mistake.user_message}

❌ {mistake.incorrect} → <b>{mistake.correct}</b>
ℹ {mistake.explanation}
📌 <b>Пример:</b> {example}
'''

    TRAIN_MISTAKES_ANSWER_IF_RIGHT = '✅ Правильный ответ'
    TRAIN_MISTAKES_ANSWER_IF_WRONG = '❌ Неправильный ответ. Правильный ответ: {}'

    @staticmethod
    def mistake(mistake: MistakeSchema) -> str:
        return MistakesTexts.MISTAKE.format(mistake=mistake, example=' | '.join(mistake.example))

    @staticmethod
    def train_mistakes_answer_if_wrong(right_answer: str) -> str:
        return MistakesTexts.TRAIN_MISTAKES_ANSWER_IF_WRONG.format(right_answer)