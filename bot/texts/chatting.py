from services.ai.base import TalkingResponse
from schemas.chatting import Mistake, MistakeSubGroup, DialogType, AnswerTalkingResult
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
    def ai_answer_mistakes(result: AnswerTalkingResult):
        def prepare_mistake(mistake: Mistake):
            print(f'{mistake=}')
            return (
                    f"❌ <s>{mistake.incorrect}</s> ➡ <b>{mistake.correct}</b>\n"
                    f"ℹ {mistake.explanation}\n"
                    f"📌 Пример: " + ' | '.join(list(map(lambda x: '<code>{}</code>'.format(x), mistake.example)))
            )
        text = '<b>Исправленный текст:</b> {}\n\n'.format(result.correct)
        text += (
                '<b>Замечания:</b>\n{}\n\n'.format(
                    '\n\n'.join(list(map(prepare_mistake, result.indications)))
                ) + '\n<b>Продолжим общение:</b>\n')
        return text

    @staticmethod
    def ai_answer(answer: TalkingResponse) -> str:
        if not answer.is_right_lang:
            return 'Пожалуйста, перейдите на английский язык'

        return ChattingTexts.ai_answer_mistakes(answer.result) + answer.result.answer.text

    @staticmethod
    def result_dialog(count_messages: int, mistakes: list[MistakeSchema] | None = None) -> str:
        def prepare_mistake(mistake: MistakeSchema):
            return (
                    f"{mistake.type.name}: <i>{mistake.incorrect}</i> ➡ <i>{mistake.correct}</i>\n"
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