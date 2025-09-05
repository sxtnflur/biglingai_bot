from aiogram.filters.callback_data import CallbackData
from bot.callbacks.base import ScrollingCallback
from typing_extensions import Optional


class MistakesListCallback(ScrollingCallback, prefix='mgl'):
    ...


class MistakesListByDialogCallback(MistakesListCallback, prefix='mistakesbydialog'):
    dialog_uuid: str


class MistakeCallback(CallbackData, prefix='mistake'):
    id: int


class MistakeGroupListCallback(ScrollingCallback, prefix='mg'):
    group: str


class TrainMistakeGroupCallback(CallbackData, prefix='tmgr'):
    group: str | None = None
    dialog_uuid: str | None = None


class TrainMistakesDialogCallback(CallbackData, prefix='tmd'):
    dialog_uuid: str


class TrainMistakeGroupAnswerCallback(CallbackData, prefix='tma'):
    is_right: bool
    mistake_id: int
    group: str | None = None
    dialog_uuid: str | None = None

    @classmethod
    def from_callback_data(cls, callback_data: str) -> Optional['TrainMistakeGroupAnswerCallback']:
        print(f'{callback_data=}')
        if not callback_data.startswith('tma:'):
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


class DeleteMistakeCallback(CallbackData, prefix='dm'):
    pre: bool = True
    is_worked_out: bool = False
    really_delete: bool = False
    mistake_id: int