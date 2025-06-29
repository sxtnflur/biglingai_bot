from enum import Enum, auto


class ChattingMessageType(int, Enum):
    text = auto()
    voice = auto()
    text_and_voice = auto()

    @property
    def label(self) -> str | None:
        labels: dict[ChattingMessageType, str] = {
            ChattingMessageType.text: 'Текст',
            ChattingMessageType.voice: 'Войсы',
            ChattingMessageType.text_and_voice: 'Войсы + текст'
        }
        return labels.get(self)


    def next(self):
        val = int(self) + 1
        if val > 3:
            val = 1
        return ChattingMessageType(val)