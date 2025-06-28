from openai import AsyncOpenAI, NotGiven, NOT_GIVEN
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel
from typing import TypeVar
import os


TSchema = TypeVar('TSchema', bound=BaseModel)


class OpenAIService:
    def __init__(self, openai_client: AsyncOpenAI, system_message: str | None = None, model: str | None = None):
        self._client = openai_client
        self.default_model = model
        self.__system_message = system_message

    def add_system_message(self, messages: list[ChatCompletionMessageParam]) -> list[ChatCompletionMessageParam]:
        if self.__system_message:
            return [{'role': 'system', 'content': self.__system_message}] + messages
        return messages

    async def _send_completition(
        self, messages: list[ChatCompletionMessageParam], model: str | None = None, **kwargs
    ):
        messages = self.add_system_message(messages)
        return await self._client.chat.completions.create(
            messages=messages, model=model or self.default_model, **kwargs
        )

    async def _send_completition_parse(
        self, schema: type[TSchema], messages: list[ChatCompletionMessageParam] | None = None, model: str | None = None, **kwargs
    ) -> TSchema:
        messages = self.add_system_message(messages)
        resp = await self._client.beta.chat.completions.parse(
            messages=messages, model=model or self.default_model, response_format=schema, **kwargs
        )
        return resp.choices[0].message.parsed

    async def send_text_get_schema(
        self, prompt: str, schema: type[TSchema], messages: list[ChatCompletionMessageParam] | None = None, model: str | None = None, **kwargs
    ) -> TSchema:
        messages = (messages or []) + [{'role': 'user', 'content': prompt}]
        return await self._send_completition_parse(
            schema=schema, messages=messages, model=model, **kwargs
        )

    async def send_text_get_text(
        self, prompt: str, messages: list[ChatCompletionMessageParam] | None = None,
        model: str | None = None, **kwargs
    ) -> str:
        messages = (messages or []) + [{'role': 'user', 'content': prompt}]
        res = await self._send_completition(
            messages, model=model, **kwargs
        )
        return res.choices[0].message.content

    async def transcript_audio(
        self, audio_path: str, model: str | None = None, prompt: str | NotGiven = NOT_GIVEN, **kwargs
    ) -> str:
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found at {audio_path}")

        # Проверка размера файла
        file_size = os.path.getsize(audio_path)
        print(f'{file_size=}')
        if file_size > 25 * 1024 * 1024:  # 25 MB
            raise ValueError("File size exceeds 25 MB limit")

        with open(audio_path, 'rb') as audio_file:
            file_size = len(audio_file.read())
            print(f'{file_size=}')
            resp = await self._client.audio.transcriptions.create(
                file=audio_file,
                model=model or self.default_model,
                prompt=prompt
            )
        return resp.text

    async def send_audio_get_schema(
        self, audio_path: str, schema: type[TSchema],
        prompt: str | None = None,
        messages: list[ChatCompletionMessageParam] | None = None,
        model: str | None = None, **kwargs
    ) -> TSchema:
        prompt_text = await self.transcript_audio(
            audio_path, model, prompt=prompt, **kwargs
        )
        return await self.send_text_get_schema(
            prompt=prompt_text, schema=schema, messages=messages, model=model, **kwargs
        )

    async def send_audio_get_text(
        self, audio_path: str,
        prompt: str | None = None,
        messages: list[ChatCompletionMessageParam] | None = None,
        model: str | None = None, **kwargs
    ) -> str:
        prompt_text = await self.transcript_audio(
            audio_path, model, prompt=prompt, **kwargs
        )
        return await self.send_text_get_text(
            prompt=prompt_text, messages=messages, model=model, **kwargs
        )