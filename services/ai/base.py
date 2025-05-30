import json
from enum import Enum, auto

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from services.ai.openai_base import OpenAIService
from pydantic import BaseModel
from typing_extensions import Literal, TypedDict, Union
from schemas.chatting import TalkingResponse, AnswerTalking, AnswerTalkingResult, AnswerTalkingIndications, AIAnswer


class Choice(BaseModel):
    text: str
    is_right: bool


class TaskWithVariants(BaseModel):
    task: str
    choices: list[Choice]


class ReadingRating(BaseModel):
    comment: str
    rate: int


class LangLearningAIService:
    def __init__(self, openai: AsyncOpenAI, model: str):
        self.openai = openai
        self.model = model

    async def choose_one_variant(
        self, prompt: str
    ) -> TaskWithVariants:
        openai_service = OpenAIService(
            openai_client=self.openai,
            system_message='''
Ты - бот для изучения английского языка.
Придумай для пользователя задание на знание английского языка с вариантами ответа.
Пояснения к заданию давай на русском языке.
Правильный ответ должен быть один
'''.strip(),
            model=self.model
        )
        return await openai_service.send_text_get_schema(
            prompt=prompt,
            schema=TaskWithVariants
        )

    # async def send_voice_read_text(
    #     self, audio_path: str, text: str
    # ) -> ReadingRating:
    #     return await self.openai.send_text_get_schema(
    #         prompt=,
    #         schema=ReadingRating
    #     )

    async def send_text_talking(
        self,
        user_text: str,
        user_lang_level: Literal['A1', 'A2', 'A3'] = 'A1',
        messages: list[ChatCompletionMessageParam] | None = None,
        response_type: Literal['text'] = 'text'
    ) -> TalkingResponse:
        openai_indications = OpenAIService(
            openai_client=self.openai,
            system_message='''
Вы - бот для изучения английского языка. В разделе "mistakes" укажите и исправьте ошибки пользователя, если таковые имеются.
Если ошибок нет, верните пустой список. Не добавляйте ничего к указаниям, в которых у пользователя нет ошибки.
Работай только с последним сообщением пользователя, но учитывай и контекс диалога.
Пишите по-русски.
Для каждой ошибки определи subgroup на основании следующих данных:
Группы ошибок: grammar / vocabulary / syntax / spelling
Далее перечисляю подгруппы для каждой группы:
1. grammar
Ошибки в структуре языка, влияющие на правильность построения предложений.

Подгруппы:
tense — неправильное использование времён (past, present, future, perfect).
subject_verb_agreement — несогласование подлежащего и глагола (She go вместо She goes).
articles — неверное поставили или не поставили артикль (a, an, the)
prepositions — ошибки в использовании предлогов (in, on, at и др.).
auxiliary_verbs — отсутствие вспомогательных глаголов (He not working).
negation — неправильное отрицание (He don’t like).

2. vocabulary
Ошибки в словарном запасе и уместности лексики.

Подгруппы:
word_choice — выбор неправильного слова (funny вместо fun).
false_friends — похожие слова, но с разным значением (actual ≠ актуальный).
collocations — неверные словосочетания (strong rain вместо heavy rain).
idioms — искажение идиом или фразеологизмов.
register_formality — неправильный стиль речи (разговорный в формальном контексте и наоборот).

3. syntax
Ошибки в порядке слов и структуре предложений.

Подгруппы:
word_order — неправильный порядок слов (She only eats vegetables vs Only she eats vegetables).
question_formation — ошибки в построении вопросов (You like it?).
relative_clauses — сложные предложения с who, which, that.
missing_elements — пропущенные элементы: подлежащее, сказуемое и др.

4. spelling
Ошибки в написании слов и расстановке знаков препинания.

Подгруппы:
spelling — ошибки в написании слов.
capitalization — ошибки в использовании заглавных букв.
punctuation — отсутствие запятых, лишние точки и др.

Уровень владения языком пользователя: {}
'''.strip().format(user_lang_level),
            model=self.model
        )
        openai_main_dialog = OpenAIService(
            openai_client=self.openai,
            model=self.model,
            system_message='''
Communicate with the user on any topic in English within the user level.
The user's level of language proficiency: {}
Don't correct the user's mistakes if they write something incorrectly.
In "is_right_lang" return false if the user is not speaking to you in English.
In "is_right_lang" write your answer. If is_right_lang=True, then the answer must be
'''.strip().format(user_lang_level)
        )
        resp_main_dialog = await openai_main_dialog.send_text_get_schema(
            prompt=user_text,
            messages=[
                         {'role': 'user',
                          'content': "My English proficiency level is A1. Please keep this in mind when communicating with me. Let's talk about something in English. Just please don't fix my mistakes, because I really don't like it."},
                         {'role': 'assistant', 'content': 'Okay! What you want to talk about?'}
                     ] + (messages or []),
            schema=AnswerTalking,
            temperature=0.7
        )
        if not resp_main_dialog.is_right_lang:
            return TalkingResponse(is_right_lang=False)

        if messages:
            resp_indications = await openai_indications.send_text_get_schema(
                schema=AnswerTalkingIndications,
                prompt=user_text,
                messages=[{
                    'role': 'user', 'content': 'Hallo! How it going?'
                }, {
                    'role': 'assistant', 'content': json.dumps(dict(indications=[
                        dict(comment='"Hallo" - Правильное написание: Hello',
                             subgroup='spelling'),
                        dict(comment='"How it going? - Нужен глагол "to be" перед подлежащим. Правильное написание: "How is it going?"',
                             subgroup='question_formation')
                    ]))
                }] + messages,
                temperature=0.3
            )
            mistakes = resp_indications.mistakes
            print(f'{resp_indications=}')
        else:
            mistakes = None

        if response_type == 'text':
            result = AnswerTalkingResult(
                answer=AIAnswer(text=resp_main_dialog.answer),
                indications=mistakes
            )
            return TalkingResponse(result=result, is_right_lang=resp_main_dialog.is_right_lang)
        raise ValueError('Такого respose_type нет: {}'.format(response_type))

    async def send_voice_talking(
        self, audio_path: str, messages: list[ChatCompletionMessageParam] | None = None,
        response_type: Literal['text'] = 'text'
    ) -> AnswerTalkingResult:
        openai_service = OpenAIService(
            openai_client=self.openai,
            system_message='''
Ты - бот для изучения английского языка. Общайся с пользователем и указывай на его ошибки.
Ошибки объясняй на русском, а общение веди на английском
'''.strip(),
            model=self.model
        )
        response_text = await openai_service.send_audio_get_schema(
            audio_path=audio_path,
            schema=AnswerTalking,
            messages=messages
        )
        if response_type == 'text':
            return AnswerTalkingResult(
                answer=AIAnswer(text=response_text.answer),
                indications=response_text.indications
            )
        raise ValueError('Такого respose_type нет: {}'.format(response_type))

#     async def rate_dialog(
#             self, messages: list[ChatCompletionMessageParam], indications: list[str]
#     ):
#         openai = OpenAIService(
#             openai_client=self.openai,
#             system_message='''
# Ты - бот для изучения английского языка
# '''.strip()
#         )
#         resp = await openai.send_text_get_schema(
#             prompt='Оцени весь диалог на знания английского и выдели основные ошибки пользователя',
#             schema=
#         )


class LangLearngingAIServiceTEST:
    def __init__(self, openai: AsyncOpenAI, model: str):
        self.openai = openai
        self.model = model

    async def choose_one_variant(
            self, prompt: str
    ) -> TaskWithVariants:
        openai_service = OpenAIService(
            openai_client=self.openai,
            system_message='''
Ты - бот для изучения английского языка.
Придумай для пользователя задание на знание английского языка с вариантами ответа.
Пояснения к заданию давай на русском языке.
Правильный ответ должен быть один
'''.strip(),
            model=self.model
        )
        return await openai_service.send_text_get_schema(
            prompt=prompt,
            schema=TaskWithVariants
        )

    async def send_text_talking(
            self,
            user_text: str,
            user_lang_level: Literal['A1', 'A2', 'B1', 'B2', 'C1', 'C2'] = 'A1',
            messages: list[dict] | None = None,
            **kwargs
    ) -> TalkingResponse:

        # Главный промпт с примером идеального ответа
        system_message = f'You are an English tutor for {user_lang_level} level students. Follow these rules:' + '''

    1. **Conversation Flow**:
    - Continue the dialogue naturally in English
    - Keep responses simple for A1-A2, more complex for B2+

    2. **Correction Rules**:
    - Analyze ONLY the user's last message
    - For each mistake provide:
      → Type (grammar/vocabulary/syntax)
      → Subgroup (see list below)
      → Incorrect → Correct
      → Explanation in Russian (detailed for A1, concise for B2+)
      → Example (2 similar sentences)

    3. **Mistake Groups** (same as before)

    4. **Response Format**:
    {{
        "response": "Your English response here",
        "mistakes": [
            {{
                "type": "grammar",
                "subgroup": "tense",
                "incorrect": "I goes",
                "correct": "I go",
                "explanation": "С 'I' используется глагол без -s в Present Simple",
                "example": ["She goes to school", "We go to work"]
            }}
        ]
    }}

    **Example Dialogue**:
    User: "I eats apple"
    {{
        "response": "Apples are delicious! What kind do you like?",
        "mistakes": [
            {{
                "type": "grammar",
                "subgroup": "subject_verb_agreement",
                "incorrect": "eats",
                "correct": "eat",
                "explanation": "С подлежащим 'I' глагол должен быть в первой форме без -s",
                "example": ["He eats sandwiches", "They eat fruit"]
            }},
            {{
                "type": "vocabulary",
                "subgroup": "articles",
                "incorrect": "apple",
                "correct": "an apple",
                "explanation": "Исчисляемые существительные в единственном числе требуют артикля",
                "example": ["I want a banana", "She has an orange"]
            }}
        ]
    }}
    '''

        response = await self.openai.chat.completions.create(
            model="gpt-4-turbo",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_message},
                *(messages or []),
                {"role": "user", "content": user_text}
            ],
            temperature=0.3  # Для более предсказуемых исправлений
        )

        try:
            data = json.loads(response.choices[0].message.content)
            return TalkingResponse(
                result=AnswerTalkingResult(
                    answer=AIAnswer(text=data["response"]),
                    indications=data.get("mistakes", [])
                ),
                is_right_lang=True
            )
        except Exception as e:
            print(f"Error parsing response: {e}")
            return TalkingResponse(is_right_lang=False)
