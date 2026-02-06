try:
    from murf import MurfRegion, AsyncMurf
except:
    pass
from services.ai import BaseAiSpeacker
from typing_extensions import AsyncIterator


class MurfService(BaseAiSpeacker):

    def __init__(self, api_key: str, model: str = 'GEN2', voice_id: str = 'en-US-alisa'):
        self.client = AsyncMurf(
            api_key=api_key
        )
        self.model = model
        self.voice_id = voice_id

    async def __parse_file_iterator(self, file_async_iterator: AsyncIterator[bytes]) -> bytes:
        res = b''
        async for a in file_async_iterator:
            res += a
        return res

    async def get_my_voices(self):
        voices = await self.client.text_to_speech.get_voices()
        for voice in voices:
            print(f'{voice=}')

    async def generate(self, text: str, **kwargs) -> bytes:
        audio_stream = self.client.text_to_speech.stream(
            text=text,
            voice_id=self.voice_id,
            model=self.model,
            multi_native_locale="en-US",
            sample_rate=44100,
            format="WAV"
        )
        return await self.__parse_file_iterator(audio_stream)

    async def speech_to_text(self, audio: bytes) -> str:
        ...