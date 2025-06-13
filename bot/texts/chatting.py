from services.ai.base import TalkingResponse
from schemas.chatting import Mistake, MistakeSubGroup, DialogType
from services.mistakes_service import MistakeSchema


class ChattingTexts:
    INSTRUCTION = '''
Как только ты нажмешь на один из режимов, я начну с тобой общаться на английском.
Ты должен поддерживать наш диалог. После каждого сообщения я буду указывать на твои ошибки,
а в конце дам тебе оценку.

Выбери режим общения:
'''

    RESULT_DIALOG_WITH_MISTAKES = '''
Неплохой результат!

Я насчитал <b>{count_mistakes}</b> ошибок из <b>{count_messages}</b> сообщений

Вот они все:
{mistakes}

Хочешь поработать над ними или начнём новый диалог?
'''
    RESULT_DIALOG_WITHOUT_MISTAKES = '''
Супер! Поздравляю!

Из <b>{count_messages}</b> сообщений ты не допустил ни одной ошибки!

Хочешь начать новый диалог?
'''

    START_BUTTON = 'Начали!'
    END_BUTTON = 'Закончить предварительно'

    @staticmethod
    def ai_answer(answer: TalkingResponse) -> str:
        if not answer.is_right_lang:
            return 'Пожалуйста, перейдите на английский язык'

        def prepare_mistake(mistake: Mistake):
            print(f'{mistake=}')
            return (
                    f"❌ <s>{mistake.incorrect}</s> → <b>{mistake.correct}</b>\n"
                    f"ℹ {mistake.explanation}\n"
                    f"📌 Пример: " + ' | '.join(list(map(lambda x: '<code>{}</code>'.format(x), mistake.example)))
            )
            # return str(mistake.model_dump())
            # return f'<b>{MistakeSubGroup(mistake.subgroup).subgroup_label.title()} ({MistakeSubGroup(mistake.subgroup).group.label.title()}):</b> {mistake.explanation}'

        text = ''
        if answer.result.indications:
            text += (
                '<b>Замечания:</b>\n{}\n\n'.format(
                    '\n\n'.join(list(map(prepare_mistake, answer.result.indications)))
                ) + '\n<b>Продолжим общение:</b>\n')
        return text + answer.result.answer.text

    @staticmethod
    def result_dialog(count_messages: int, mistakes: list[MistakeSchema] | None = None) -> str:
        def prepare_mistake(mistake: MistakeSchema):
            return (
                    f"<s>{mistake.incorrect}</s> → <b>{mistake.correct}</b>\n"
                    # f"ℹ {mistake.explanation}\n"
                    # f"📌 Пример: " + ' | '.join(list(map(lambda x: '<code>{}</code>'.format(x), mistake.example)))
            )
            # return f'<b>{mistake.subgroup.subgroup_label.title()} ({mistake.subgroup.group.label}):</b> {mistake.comment}'

        if mistakes:
            return ChattingTexts.RESULT_DIALOG_WITH_MISTAKES.format(
                count_messages=count_messages,
                count_mistakes=len(mistakes),
                mistakes='\n'.join(list(map(prepare_mistake, mistakes)))
            )
        else:
            return ChattingTexts.RESULT_DIALOG_WITHOUT_MISTAKES.format(
                count_messages=count_messages
            )

    @staticmethod
    def dialog_type_label(dialog_type: DialogType) -> str:
        labels = {
            DialogType.SMALL_TALK: '💬 Короткие диалоги',
            DialogType.LONG_TALK: '🗣️ Глубокий разговор',
            DialogType.ROLE_PLAY: '🎭 Ролевая игра',
            DialogType.STORY: '📖 Совместная история',
            DialogType.NEWS: '📰 Новости',
            DialogType.DEBATE: '⚖ Дебаты',
            DialogType.CULTURE: '🌍 Культура'
        }
        return labels[dialog_type]