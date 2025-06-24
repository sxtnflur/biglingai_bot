from pydantic import BaseModel


class GrammarEdit(BaseModel):
    type: str
    incorrect: str
    correct: str


class GrammarResult(BaseModel):
    correct: str
    original: str
    edits: list[GrammarEdit]