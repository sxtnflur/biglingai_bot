from schemas.grammar import GrammarResult, GrammarEdit
import errant
from gradio_client import Client, handle_file


class GrammarAIService:
    def __init__(self):
        self.gr_client = Client("gaur3009/Speech_grammar")
        self.annotator = errant.load('en')

    async def get_edits(self, orig: str, corr: str) -> list[GrammarEdit]:
        orig = self.annotator.parse(orig)
        cor = self.annotator.parse(corr)
        alignment = self.annotator.align(orig, cor)
        edits = self.annotator.merge(alignment)

        if len(edits) == 0:
            return []

        edit_annotations = []
        for e in edits:
            e = self.annotator.classify(e)
            edit_annotations.append(
                GrammarEdit(
                    type=e.type[2:],
                    incorrect=e.o_str,
                    correct=e.c_str
                ))

        if len(edit_annotations) > 0:
            return edit_annotations
        else:
            return []

    def _post_process_result(self, correct: str, orig: str) -> str:
        if correct.endswith('.') and not orig.endswith('.'):
            return correct[:-1]
        return correct

    async def correct_text(self, text: str) -> str:
        result = self.gr_client.submit(
            text=text,
            audio=None,
            api_name="//predict"
        )
        correct: str = result.result()[0]
        print(f'{correct=}')
        return self._post_process_result(correct, text)

    async def process_text(self, text: str) -> GrammarResult:
        corr = await self.correct_text(text)
        return GrammarResult(
            correct=corr,
            original=text,
            edits=await self.get_edits(orig=text, corr=corr)
        )

    async def correct_audio(self, audio_path: str) -> str:
        result = self.gr_client.submit(
            text=None,
            audio=handle_file(audio_path),
            api_name="//predict"
        )
        correct: str = result.result()[0]
        print(f'{correct=}')
        return correct

    async def process_audio(self, audio_path: str) -> GrammarResult:
        corr = await self.correct_audio(audio_path)
        return GrammarResult(
            correct=corr,
            original=None,
            edits=await self.get_edits(orig='', corr=corr)
        )

    async def lambda_(self):
        res = self.gr_client.predict(
            api_name="/lambda"
        )
        print(f'{res=}')