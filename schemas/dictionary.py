from pydantic import BaseModel


class AddDictionaryWord(BaseModel):
    word: str
    ru_word: str
    level: int


class UserWord(BaseModel):
    learning_rate: int
    can_be_mark_as_worked: bool
    is_worked: bool

    class Config: from_attributes = True


class DictionaryWord(AddDictionaryWord):
    id: int

    class Config: from_attributes = True


class DictionaryWordWithUserInfo(BaseModel):
    word: DictionaryWord
    user_info: UserWord | None = None


class UserDictionaryWord(BaseModel):
    learning_rate: int
    can_be_mark_as_worked: bool
    is_worked: bool
    word: DictionaryWord

    class Config: from_attributes = True



class AIGeneratedDictionaryWord(BaseModel):
    word: AddDictionaryWord | None = None
    is_en_word: bool = True