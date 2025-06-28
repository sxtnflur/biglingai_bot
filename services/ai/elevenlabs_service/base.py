from typing_extensions import Protocol


class BaseAiSpeacker(Protocol):

    async def generate(self, text: str, **kwargs) -> bytes: ...
    async def speech_to_text(self, audio: bytes) -> str: ...