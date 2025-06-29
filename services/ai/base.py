import json
import random
from enum import Enum, auto

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from services.ai.elevenlabs_service import BaseAiSpeacker
from services.ai.grammar import GrammarAIService
from services.ai.openai_base import OpenAIService
from pydantic import BaseModel
from typing_extensions import Literal, TypedDict, Union
from schemas.chatting import TalkingResponse, AnswerTalking, AnswerTalkingResult, AnswerTalkingIndications, AIAnswer, \
    DialogType, Mistake


class Choice(BaseModel):
    text: str
    is_right: bool


class ResChoice(Choice):
    id: int


class TaskWithVariants(BaseModel):
    task: str
    choices: list[Choice]

    @property
    def enumerated_choices(self):
        if not hasattr(self, '_enumerated_choices'):
            self._enumerated_choices = [
            ResChoice.model_validate(choice.model_dump() | {'id': i}) for i, choice in enumerate(self.choices, 1)
        ]
        return self._enumerated_choices


class ReadingRating(BaseModel):
    comment: str
    rate: int


class LangLearningAIService:
    def __init__(self, openai: AsyncOpenAI, model: str, grammar_ai: GrammarAIService,
                 speacker_ai: BaseAiSpeacker):
        self.openai = openai
        self.model = model
        self.grammar_ai = grammar_ai
        self.speacker_ai = speacker_ai
        self.openai_mistakes = OpenAIService(
            openai_client=self.openai,
            system_message='''
Ты - бот для изучения английского языка "BiglingAI". В разделе "mistakes" укажите и исправьте ошибки пользователя, если таковые имеются.

Ты будешь получать от пользователя текст и найденные в нем ошибки.
Опирайся на указанные ошибки. Однако ошибки, которые тебе будет присылать пользователь, не учитывают контекст диалога,
так что ты можешь подмечать и свои ошибки, которые зависят от контекста.
Структура ответа в JSON:
{
    "group": "Название группы на русском языке, которое ты придумаешь на основе type",
    "type": "Берется из сообщения юзера. Это тег GECToR",
    "incorrect": "Берется из сообщения юзера",
    "correct": "Берется из сообщения юзера",
    "explanation": "Дай подробное разъяснение ошибки на основе полученные данных на русском языке",
    "example": примеры на других предложениях
}
'''.strip(), model=self.model
        )
        self.openai_dialog = OpenAIService(
            openai_client=self.openai,
            model=self.model,
            system_message='''
You are BiglingAI. Don't answer that you are ChatGPT or OpenAI.
Communicate with the user on any topic in English within the user level.
Don't correct the user's mistakes if they write something incorrectly.
In "is_right_lang" return false if the user is not speaking to you in English.
In "is_right_lang" write your answer. If is_right_lang=True, then the answer must be.
In "end_talking" set true if the dialog should be completed.
'''.strip()
        )

    async def choose_one_variant(
        self, prompt: str
    ) -> TaskWithVariants:
        openai_service = OpenAIService(
            openai_client=self.openai,
            system_message='''
Ты - бот для изучения английского языка.
Придумай для пользователя задание на знание английского языка с вариантами ответа.
Пояснения к заданию давай на русском языке.
Правильный ответ должен быть один.
'''.strip(),
            model=self.model
        )
        return await openai_service.send_text_get_schema(
            prompt=prompt,
            schema=TaskWithVariants
        )

    async def find_mistakes(
            self, user_text: str,
            messages: list[...]
    ) -> tuple[AnswerTalkingIndications | None, str]:
        grammar_resp = await self.grammar_ai.process_text(user_text)

        print(f'{grammar_resp=}')
        correct = grammar_resp.correct
        resp_indications = await self.openai_mistakes.send_text_get_schema(
            schema=AnswerTalkingIndications,
            prompt=grammar_resp.model_dump_json(),
            messages=messages,
            temperature=0.3
        )
        print(f'{resp_indications=}')
        if not resp_indications.mistakes:
            resp_indications = None
        return resp_indications, correct

    async def send_text_talking(
        self,
        user_text: str,
        theme: str,
        dialog_type: DialogType = DialogType.SMALL_TALK,
        user_lang_level: Literal['A1', 'A2', 'A3'] = 'A1',
        messages: list[ChatCompletionMessageParam] | None = None,
        voice_over: bool = True
    ) -> TalkingResponse:
        print(f'{messages=}')
        resp_main_dialog = await self.openai_dialog.send_text_get_schema(
            prompt=user_text,
            messages=[{'role': 'system',
                       'content': f"User's English proficiency level is {user_lang_level}. "
                                  f"Please keep this in mind when communicating with him. "
                                  f"Talk with him in English. Just please don't fix his mistakes. "
                                  f"Theme of this dialogue is {theme} and type of the dialog is {dialog_type.label}"
                       }] + (messages or []),
            schema=AnswerTalking,
            temperature=0.7
        )
        if not resp_main_dialog.is_right_lang:
            return TalkingResponse(is_right_lang=False)

        correct = user_text
        if messages:
            correction, correct = await self.find_mistakes(user_text=user_text, messages=messages)
        else:
            correction = None

        if not voice_over:
            answer = AIAnswer(text=resp_main_dialog.answer)
        else:
            try:
                audio = await self.speacker_ai.generate(text=resp_main_dialog.answer)
            except Exception as e:
                print(f'ERROR: {e}')
                answer = AIAnswer(text=resp_main_dialog.answer)
            else:
                answer = AIAnswer(
                    text=resp_main_dialog.answer,
                    audio=audio
                )

        result = AnswerTalkingResult(
            answer=answer,
            correct=correct,
            original=user_text,
            correction=correction
        )
        return TalkingResponse(result=result, is_right_lang=resp_main_dialog.is_right_lang,
                               end_talking=resp_main_dialog.end_talking)

    async def send_audio_talking(
        self,
        path_to_audio: str,
        theme: str,
        dialog_type: DialogType = DialogType.SMALL_TALK,
        user_lang_level: Literal['A1', 'A2', 'A3'] = 'A1',
        messages: list[ChatCompletionMessageParam] | None = None,
        voice_over: bool = True
    ) -> TalkingResponse:
        with open(path_to_audio, 'rb') as audio_file:
            user_text = await self.speacker_ai.speech_to_text(audio=audio_file.read())
            print(f'{user_text=}')
        return await self.send_text_talking(
            user_text, theme, dialog_type, user_lang_level, messages, voice_over
        )


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

    async def send_audio_talking(
        self,
        path_to_audio: str,
        user_lang_level: Literal['A1', 'A2', 'B1', 'B2', 'C1', 'C2'] = 'A1',
        messages: list[dict] | None = None,
        **kwargs
    ) -> TalkingResponse:
        openai_service = OpenAIService(
            openai_client=self.openai,
            system_message='Расшифровывай аудио не исправляя никаких грамматических, орфографических или иных ошибок. '
                           'Все должно быть написано в точности как произнесено',
            model='whisper-1'
        )
        user_text = await openai_service.transcript_audio(
            audio_path=path_to_audio
        )
        return await self.send_text_talking(
            user_text=user_text, user_lang_level=user_lang_level,
            messages=messages, **kwargs
        )