from typing_extensions import Protocol


class BaseAiSpeacker(Protocol):

    async def generate(self, text: str, **kwargs) -> bytes: ...