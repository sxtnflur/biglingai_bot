from gramformer import Gramformer
from schemas.grammar import GrammarResult, GrammarEdit


class GrammarAIService:
    def __init__(self):
        self.gf = Gramformer(models=1, use_gpu=False)

    async def process_text(self, text: str) -> GrammarResult:
        corrected_sentences = self.gf.correct(text, max_candidates=1)
        results = []
        for corr in corrected_sentences:
            print(f'{corr=}')
            edits = self.gf.get_edits(text, corr)
            results.append(
                GrammarResult(
                    correct=corr,
                    original=text,
                    edits=list(map(lambda x: GrammarEdit(type=x[0], incorrect=x[1], correct=x[4]), edits))
                )
            )
        print(f'{results=}')
        return results[0]