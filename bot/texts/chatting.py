from enums import ChattingMessageType
from services.ai.base import TalkingResponse
from schemas.chatting import Mistake, MistakeSubGroup, DialogType, AnswerTalkingResult, AnswerTalkingIndications
from services.mistakes_service import MistakeSchema


class ChattingTexts:
    START = '''
💬 <b>Чаттинг</b>

<blockquote expandable>Здесь ты можешь пообщаться со мной на заготовленные темы.
Ты должен поддерживать наш диалог.
После каждого неверного сообщения я буду указывать на твои ошибки,
а в конце дам тебе оценку</blockquote>

<i>Выбери формат, в котором я буду с тобой общаться:
(🖊️ Текст | 🗣️ Голос | 🗣️ Голос + 🖊️ Текст)

а после нажми "⏩ Выбрать режим"</i>
'''

    INSTRUCTION = '''
Как только ты нажмешь на один из режимов, мы начнем общение

<i>Скорее выбирай режим:</i>
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

    CHOOSE_DIALOG_MODE = '⏩ Выбрать режим'
    END_BUTTON = 'Закончить предварительно'
    IF_IS_NOT_ENG_MESSAGE = 'Пожалуйста, перейдите на английский язык'

    NOT_ENOUGH_MESSAGES_TO_RATE_DIALOG = 'Слишком мало сообщений для оценки диалога. ' \
                                         'Надеюсь, в следующий раз пообщаемся побольше'

    @staticmethod
    def dialog_message_type_button(current_value: ChattingMessageType):
        return 'Формат ответа: ' + current_value.label

    @staticmethod
    def ai_answer_mistakes(correction: AnswerTalkingIndications):
        def prepare_mistake(mistake: Mistake):
            print(f'{mistake=}')
            return (
                    f"❌ <s>{mistake.incorrect}</s> ➡ <b>{mistake.correct}</b>\n"
                    f"<blockquote expandable>ℹ {mistake.explanation}</blockquote>\n"
                    f"📌 <b>Например:</b> " + ' | '.join(list(map(lambda x: '<blockquote>{}</blockquote>'.format(x), mistake.example)))
            )
        text = '<b>Исправленный текст:</b> {}\n\n'.format(correction.correct)
        text += (
                '<b>Замечания:</b>\n{}\n\n'.format(
                    '\n\n'.join(list(map(prepare_mistake, correction.mistakes)))
                ) + '\n<b>Продолжим общение:</b>\n')
        return text

    @staticmethod
    def ai_answer(result: AnswerTalkingResult) -> str:
        if result.correction:
            return ChattingTexts.ai_answer_mistakes(result.correction) + result.answer.text
        else:
            return result.answer.text

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