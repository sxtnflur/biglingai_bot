from aiogram.filters.callback_data import CallbackData
from bot.callbacks.base import ScrollingCallback
from typing_extensions import Optional


class MistakesListCallback(ScrollingCallback, prefix='mistakes-groups-list'):
    ...


class MistakesListByDialogCallback(MistakesListCallback, prefix='mistakesbydialog'):
    dialog_uuid: str


class MistakeCallback(CallbackData, prefix='mistake'):
    id: int


class MistakeGroupListCallback(ScrollingCallback, prefix='mistake-group'):
    group: str


class TrainMistakeGroupCallback(CallbackData, prefix='train-mistake-group'):
    group: str

class TrainMistakesDialogCallback(CallbackData, prefix='train-mistake-dialog'):
    dialog_uuid: str


class TrainMistakeGroupAnswerCallback(CallbackData, prefix='train-mistake-group-answer'):
    is_right: bool
    mistake_id: int
    group: str

    @classmethod
    def from_callback_data(cls, callback_data: str) -> Optional['TrainMistakeGroupAnswerCallback']:
        print(f'{callback_data=}')
        if not callback_data.startswith('train-mistake-group-answer:'):
            return

        try:
            args = tuple(callback_data.split(':'))
            return TrainMistakeGroupAnswerCallback(
                is_right=bool(int(args[1])),
                mistake_id=int(args[2]),
                group=args[3]
            )
        except:
            return