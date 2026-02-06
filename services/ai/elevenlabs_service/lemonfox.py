import httpx
from .base import BaseAiSpeacker


class LemonfoxService(BaseAiSpeacker):
    def __init__(self, api_key: str):
        self.base_url = 'https://api.lemonfox.ai/v1'
        self.client = httpx.AsyncClient(headers={
          "Authorization": f"Bearer {api_key}",
          "Content-Type": "application/json"
        })

    async def generate(self, text: str, **kwargs) -> bytes:
        response = await self.client.post(
            url=self.base_url + '/audio/speech',
            json=dict(
                input=text,
                voice='heart',
                response_format='mp3'
            )
        )
        return response.read()
