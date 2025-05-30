from enum import Enum, auto, StrEnum

from pydantic import BaseModel


class AIAnswer(BaseModel):
    text: str
    audio: bytes | None = None


class Group:
    label: str
    value: int

    @staticmethod
    def get_group_by_value(v: int):
        groups = [
            GrammarSubGroup,
            LexicalSubGroup,
            SpellingSubGroup,
            SyntaxSubGroup
        ]
        return groups[v]


class GroupEnum(StrEnum):
    grammar = auto()
    lexixal = auto()
    vocabulary = auto()
    spelling = auto()


class GrammarSubGroup(Group):
    label = 'Грамматика'
    value = 0


class LexicalSubGroup(Group):
    label = 'Лексика'
    value = 1


class SpellingSubGroup(Group):
    label = 'Орфография'
    value = 2


class SyntaxSubGroup(Group):
    label = 'Синтакс'
    value = 3


class MistakeSubGroup(StrEnum):
    tense = auto()
    subject_verb_agreement = auto()
    articles = auto()
    prepositions = auto()
    plural_singular = auto()
    auxiliary_verbs = auto()
    negation = auto()

    word_choice = auto()
    collocations = auto()
    idioms = auto()
    false_translator_friends = auto()
    register_formality = auto()

    spelling = auto()
    capitalization = auto()
    punctuation = auto()

    word_order = auto()
    question_formation = auto()
    relative_clauses = auto()
    missing_elements = auto()

    @property
    def subgroup_label(self) -> str:
        labels = {
            MistakeSubGroup.tense: 'Времена',
            MistakeSubGroup.subject_verb_agreement: 'Согласование подлежащего и сказуемого',
            MistakeSubGroup.articles: 'Артикли',
            MistakeSubGroup.prepositions: 'Предлоги',
            MistakeSubGroup.auxiliary_verbs: 'Вспомогательные глаголы',
            MistakeSubGroup.negation: 'Неправильное отрицание',

            MistakeSubGroup.word_choice: 'Выбор слов',
            MistakeSubGroup.collocations: 'Словосочетания',
            MistakeSubGroup.false_translator_friends: 'Ложные друзья переводчика',
            MistakeSubGroup.register_formality: 'Неуместный стиль',
            MistakeSubGroup.idioms: 'Фразеологизмы и идиомы',

            MistakeSubGroup.spelling: 'Написание слов',
            MistakeSubGroup.capitalization: 'Заглавные буквы',
            MistakeSubGroup.punctuation: 'Пунктуация',

            MistakeSubGroup.word_order: 'Порядок слов',
            MistakeSubGroup.question_formation: 'Построение вопросов',
            MistakeSubGroup.relative_clauses: 'Сложные предложения',
            MistakeSubGroup.missing_elements: 'Пропущенные элементы'
        }
        return labels.get(self)

    @property
    def group(self) -> Group:
        groups = {
            MistakeSubGroup.tense: GrammarSubGroup,
            MistakeSubGroup.subject_verb_agreement: GrammarSubGroup,
            MistakeSubGroup.articles: GrammarSubGroup,
            MistakeSubGroup.prepositions: GrammarSubGroup,
            MistakeSubGroup.auxiliary_verbs: GrammarSubGroup,
            MistakeSubGroup.negation: GrammarSubGroup,

            MistakeSubGroup.word_choice: LexicalSubGroup,
            MistakeSubGroup.collocations: LexicalSubGroup,
            MistakeSubGroup.false_translator_friends: LexicalSubGroup,
            MistakeSubGroup.register_formality: LexicalSubGroup,
            MistakeSubGroup.idioms: LexicalSubGroup,

            MistakeSubGroup.spelling: SpellingSubGroup,
            MistakeSubGroup.capitalization: SpellingSubGroup,
            MistakeSubGroup.punctuation: SpellingSubGroup,

            MistakeSubGroup.word_order:  SyntaxSubGroup,
            MistakeSubGroup.question_formation:  SyntaxSubGroup,
            MistakeSubGroup.relative_clauses:  SyntaxSubGroup,
            MistakeSubGroup.missing_elements: SyntaxSubGroup
        }
        return groups.get(self)


class AnswerTalking(BaseModel):
    answer: str
    is_right_lang: bool = True


class AnswerTalkingIndications(BaseModel):
    mistakes: list['Mistake'] | None = None


class AnswerTalkingResult(BaseModel):
    answer: 'AIAnswer'
    indications: list['Mistake'] | None = None


class TalkingResponse(BaseModel):
    result: AnswerTalkingResult | None = None
    is_right_lang: bool



# class MistakeGroup(Enum):
#     grammar = auto()
#     vocabulary = auto()
#     spelling = auto()
#     punctuation = auto()
#     coherence = auto()
#     style = auto()
#
#     @property
#     def label(self) -> str:
#         labels = {
#             MistakeGroup.grammar: 'Грамматика',
#             MistakeGroup.vocabulary: 'Словарный запас',
#             MistakeGroup.spelling: 'Орфография',
#             MistakeGroup.punctuation: 'Пунктуация',
#             MistakeGroup.coherence: 'Связность',
#             MistakeGroup.style: 'Стиль'
#         }
#         return labels.get(self)


class Mistake(BaseModel):
    group: str
    subgroup: str
    incorrect: str
    correct: str
    explanation: str
    example: list[str]


class RateDialog(BaseModel):
    comment: str
    grammatical_accurancy: int
    mistakes: list[Mistake] | None = None