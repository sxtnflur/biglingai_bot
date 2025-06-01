

class OpenAIFunctions:
    async def suggest_raising_level(self) -> None: ...
    async def suggest_lowering_level(self) -> None: ...
    async def suggest_add_word_to_dictionary(self, word: str) -> None: ...


# class OpenAIWorkOutMistakeFunctions:
#     async def suggest_delete_error(self):