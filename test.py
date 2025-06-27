# grammar_corrector.py
import asyncio

from depends import speacker_ai


def test_speacker_ai_get_data():
    async def do():
        models = await speacker_ai.get_models()
        voices = await speacker_ai.get_voices()

        print(f'{models=}')
        print(f'{voices=}')
    asyncio.get_event_loop().run_until_complete(do())


# Пример запуска:
if __name__ == "__main__":
    test_speacker_ai_get_data()