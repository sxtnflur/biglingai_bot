from typing import AsyncIterator

from elevenlabs import VoiceSettings
from elevenlabs.client import AsyncElevenLabs
from enum import Enum
from config import settings
from httpx import AsyncClient, Proxy
from .base import BaseAiSpeacker


class OutputFormatEnum(str, Enum):
    mp3_44100_32 = "mp3_44100_32"
    mp3_22050_32 = "mp3_22050_32"
    mp3_44100_64 = "mp3_44100_64"
    mp3_44100_96 = "mp3_44100_96"
    mp3_44100_128 = "mp3_44100_128"
    mp3_44100_192 = "mp3_44100_192"
    pcm_16000 = "pcm_16000"
    pcm_22050 = "pcm_22050"
    pcm_24000 = "pcm_24000"
    pcm_44100 = "pcm_44100"
    ulaw_8000 = "ulaw_8000"


class Elevenlabs(BaseAiSpeacker):
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.client = AsyncElevenLabs(
            api_key=api_key,
        )

    async def get_models(self):
        return await self.client.models.list()

    async def get_voices(self):
        return await self.client.voices.get_all()

    async def __parse_file_iterator(self, file_async_iterator: AsyncIterator[bytes]) -> bytes:
        res = b''
        async for a in file_async_iterator:
            res += a
        return res

    async def generate(self, text: str, voice: str = settings.ELEVENLABS_DEFAULT_VOICE_ID, **kwargs) -> bytes:
        # audio = self.client.text_to_speech.convert(
        #     text=text, voice_id=voice, model_id=self.model,
        #     voice_settings=VoiceSettings(speed=kwargs.get('speed')) if kwargs.get('speed') else None
        # )
        audio = self.client.text_to_speech.stream(
            text=text, voice_id=voice, model_id=self.model,
            voice_settings=VoiceSettings(speed=kwargs.get('speed')) if kwargs.get('speed') else None
        )
        return await self.__parse_file_iterator(audio)

    async def speech_to_text(self, audio: bytes) -> str:
        res = await self.client.speech_to_text.convert(
            model_id='scribe_v1',
            file=audio
        )
        return res.text

    async def speech_to_speech(self, audio: bytes, voice: str = settings.ELEVENLABS_DEFAULT_VOICE_ID) -> bytes:
        result_audio = await self.client.speech_to_speech.convert(
            voice_id=voice,
            audio=audio,
            output_format=OutputFormatEnum.mp3_22050_32,
            model_id=settings.apis.elevenlabs.model,

        )
        return await self.__parse_file_iterator(result_audio)