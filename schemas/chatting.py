from enum import Enum, auto, StrEnum
import random

from pydantic import BaseModel


class MistakeType(BaseModel):
    key: str
    name: str
    class Config: from_attributes = True


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
    end_talking: bool = False


class AnswerTalkingIndications(BaseModel):
    mistakes: list['Mistake'] | None = None


class AnswerTalkingResult(BaseModel):
    answer: 'AIAnswer'
    correct: str
    indications: list['Mistake'] | None = None


class TalkingResponse(BaseModel):
    result: AnswerTalkingResult | None = None
    is_right_lang: bool
    end_talking: bool


class MistakeGroup(StrEnum):
    grammar = auto()
    vocabulary = auto()
    syntax = auto()
    spelling = auto()




class Mistake(BaseModel):
    # group: MistakeGroup
    # subgroup: MistakeSubGroup
    group: str
    type: str
    incorrect: str
    correct: str
    explanation: str
    example: list[str]


class DialogType(StrEnum):
    SMALL_TALK = auto()
    LONG_TALK = auto()
    ROLE_PLAY = auto()
    DEBATE = auto()
    STORY = auto()
    NEWS = auto()
    CULTURE = auto()

    def prompt(self, theme: str) -> str:
        return dialog_types_prompts[self].format(theme=theme)

    @property
    def themes(self) -> list[str]:
        return dialog_types_themes[self]

    @property
    def random_theme(self) -> str:
        return random.choice(self.themes)

    @property
    def label(self) -> str:
        labels = {
            DialogType.SMALL_TALK: 'Small Talk',
            DialogType.LONG_TALK: 'Long Talk',
            DialogType.ROLE_PLAY: 'Ролевая игра',
            DialogType.STORY: 'История',
            DialogType.NEWS: 'Новости',
            DialogType.DEBATE: 'Дебаты',
            DialogType.CULTURE: 'Культура'
        }
        return labels[self]



dialog_types_prompts = {
    DialogType.SMALL_TALK: "Keep conversation short (3-5 exchanges). Current theme: {theme}",
    DialogType.LONG_TALK: "Ask follow-up questions to continue topic: {theme}",
    DialogType.ROLE_PLAY: "Have a role-playing dialogue on the topic: {theme}",
    DialogType.DEBATE: "Take opposite position on: {theme}",
    DialogType.STORY: "Build story together. Correct mistakes subtly. Theme: {themen}",
    DialogType.NEWS: "Discuss this news: {theme}. Ask user's opinion.",
    DialogType.CULTURE: "Explain cultural aspect: {theme}. Give examples."
}

dialog_types_themes = {
    DialogType.SMALL_TALK: [
        "Weather",
        "Food preferences",
        "Weekend plans",
        "Hobbies",
        "Current mood",
        "Favorite music",
        "Pets",
        "Travel experiences",
        "Movies/TV shows",
        "Sports"
    ],

    DialogType.LONG_TALK: [
        "Work-life balance",
        "Cultural differences",
        "Personal goals",
        "Technology impact",
        "Education system",
        "Environmental issues",
        "Future predictions",
        "Social media influence",
        "Book recommendations",
        "Life philosophies"
    ],

    DialogType.ROLE_PLAY: [
        "Restaurant ordering",
        "Hotel check-in",
        "Job interview",
        "Doctor appointment",
        "Airport security",
        "Store return",
        "Bank loan application",
        "Car rental",
        "Tourist asking directions",
        "Neighbor complaint"
    ],

    DialogType.DEBATE: [
        "Remote work vs office",
        "Social media: pros and cons",
        "Uniforms in schools",
        "Space exploration funding",
        "Gaming addiction",
        "Universal basic income",
        "Animal testing",
        "Censorship in art",
        "Gun control laws",
        "Capital punishment"
    ],

    DialogType.STORY: [
        "Mystery in old mansion",
        "Alien first contact",
        "Time travel mishap",
        "Zombie apocalypse",
        "Superhero origin",
        "Haunted vacation",
        "Robot rebellion",
        "Lost civilization",
        "Secret agent mission",
        "Magical school adventure"
    ],

    DialogType.NEWS: [
        "Breakthrough in medicine",
        "New tech gadget release",
        "Climate change report",
        "Sports championship results",
        "Political election updates",
        "Celebrity culture analysis",
        "Space mission news",
        "Economic trends",
        "Wildlife conservation",
        "AI development"
    ],

    DialogType.CULTURE: [
        "Holiday traditions",
        "Business etiquette",
        "Dating customs",
        "Superstitions",
        "Idioms explained",
        "Gestures meanings",
        "Traditional foods",
        "Festivals worldwide",
        "Work culture differences",
        "Family structures"
    ]
}