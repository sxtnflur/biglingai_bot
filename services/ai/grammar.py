from schemas.grammar import GrammarResult, GrammarEdit
import errant
from gradio_client import Client


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

    async def correct_text(self, text: str) -> str:
        result = self.gr_client.submit(
            text=text,
            audio=None,
            api_name="//predict"
        )
        return result.result()[0]

    async def process_text(self, text: str) -> GrammarResult:
        corr = await self.correct_text(text)
        return GrammarResult(
            correct=corr,
            original=text,
            edits=await self.get_edits(orig=text, corr=corr)
        )