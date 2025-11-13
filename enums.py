from enum import Enum, auto


class ChattingMessageType(int, Enum):
    text = auto()
    voice = auto()
    text_and_voice = auto()

    @property
    def label(self) -> str | None:
        labels: dict[ChattingMessageType, str] = {
            ChattingMessageType.text: '🖊️ Текст',
            ChattingMessageType.voice: '🗣️ Голос',
            ChattingMessageType.text_and_voice: '🗣️ Голос + 🖊️ Текст'
        }
        return labels.get(self)

    def next(self):
        val = int(self) + 1
        if val > 3:
            val = 1
        return ChattingMessageType(val)


class Audience(Enum):
    all = auto()
    paid = auto()
    not_paid = auto()

    @property
    def label(self) -> str:
        labels = {
            Audience.all: 'Все',
            Audience.paid: 'Оплатившие',
            Audience.not_paid: 'Не оплатившие'
        }
        return labels.get(self)