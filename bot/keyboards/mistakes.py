from uuid import UUID

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from schemas.chatting import MistakeSubGroup
from services.ai.base import Choice, ResChoice
from services.mistakes_service import MistakeSchema, MistakeGroupSchema
from .base import BaseKeyboards
from ..callbacks.mistakes import MistakesListCallback, MistakesListByDialogCallback, MistakeCallback, \
    MistakeGroupListCallback, TrainMistakeGroupAnswerCallback, TrainMistakeGroupCallback, TrainMistakesDialogCallback, \
    DeleteMistakeCallback
import textwrap

from ..texts.base import BaseTexts
from ..texts.mistakes import MistakesTexts


class MistakesKeyboards:
    @staticmethod
    def mistake_groups_list(
        groups: list[MistakeGroupSchema],
        page: int,
        limit: int
    ) -> InlineKeyboardMarkup:
        return BaseKeyboards.create_scrolling_kb(
            page=page, callback_data=MistakesListCallback,
            get_btn=lambda m: InlineKeyboardButton(
                text='{} ({})'.format(m.type.name, m.count_mistakes),
                callback_data=MistakeGroupListCallback(group=m.type.key.replace(':', '&')).pack()
            ),
            limit=limit, objs=groups,
            additional_btns=[[InlineKeyboardButton(text=BaseTexts.BACK, callback_data='start')]],
            width=1
        )

    @staticmethod
    def mistakes_by_dialog_list(
        mistakes: list[MistakeSchema],
        page: int,
        limit: int,
        dialog_uuid: UUID
    ) -> InlineKeyboardMarkup:
        def get_btn(x: MistakeSchema) -> InlineKeyboardButton:
            return InlineKeyboardButton(
                text=textwrap.fill(text=x.incorrect, width=10) + ' [{}]'.format(x.subgroup.subgroup_label.capitalize()),
                callback_data=MistakeCallback(id=x.id).pack()
            )

        return BaseKeyboards.create_scrolling_kb(
            page=page, callback_data=MistakesListByDialogCallback,
            get_btn=get_btn, limit=limit, objs=mistakes,
            pag_btn_additional_kwargs=dict(dialog_uuid=dialog_uuid)
        )

    @staticmethod
    def result_chatting_dialog(
        dialog_uuid: UUID, has_mistakes: bool
    ) -> InlineKeyboardMarkup:
        if has_mistakes:
            return InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=MistakesTexts.WORK_OUT_MISTAKE_BUTTON,
                    callback_data=MistakesListCallback().pack()  # MistakesListByDialogCallback(dialog_uuid=dialog_uuid.__str__()).pack()
                )],
                [InlineKeyboardButton(
                    text=MistakesTexts.START_NEW_DIALOG,
                    callback_data='chatting_mode_start'
                )],
                [InlineKeyboardButton(
                    text=BaseTexts.MAIN_MENU_BUTTON, callback_data='start'
                )]
            ])
        else:
            return InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=MistakesTexts.START_NEW_DIALOG,
                    callback_data='chatting_mode_start'
                )],
                [InlineKeyboardButton(
                    text=BaseTexts.MAIN_MENU_BUTTON, callback_data='start'
                )]
            ])

    @staticmethod
    def mistakes_list(
        mistakes: list[MistakeSchema],
        page: int,
        limit: int,
        group: str
    ) -> InlineKeyboardMarkup:
        def get_btn(x: MistakeSchema) -> InlineKeyboardButton:
            return InlineKeyboardButton(
                text=textwrap.fill(text=x.incorrect, width=10),
                callback_data=MistakeCallback(id=x.id).pack()
            )
        return BaseKeyboards.create_scrolling_kb(
            page=page, callback_data=MistakeGroupListCallback,
            get_btn=get_btn,
            limit=limit,
            objs=mistakes,
            pag_btn_additional_kwargs=dict(group=group),
            additional_btns=[[
                InlineKeyboardButton(
                    text=MistakesTexts.WORK_OUT_MISTAKE_BUTTON,
                    callback_data=TrainMistakeGroupCallback(group=group).pack()
                )
            ], [InlineKeyboardButton(
                text=BaseTexts.BACK,
                callback_data=MistakesListCallback().pack()
            )]]
        )

    @staticmethod
    def mistakes_list_by_dialog_uuid(
        mistakes: list[MistakeSchema],
        page: int, limit: int,
        dialog_uuid: str
    ):
        def get_btn(x: MistakeSchema) -> InlineKeyboardButton:
            return InlineKeyboardButton(
                text=textwrap.fill(text=x.explanation, width=10),
                callback_data=MistakeCallback(id=x.id).pack()
            )

        return BaseKeyboards.create_scrolling_kb(
            page=page, callback_data=MistakeGroupListCallback,
            get_btn=get_btn,
            limit=limit,
            objs=mistakes,
            pag_btn_additional_kwargs=dict(dialog_uuid=dialog_uuid),
            additional_btns=[[
                InlineKeyboardButton(
                    text=MistakesTexts.WORK_OUT_MISTAKE_BUTTON,
                    callback_data=TrainMistakesDialogCallback(dialog_uuid=dialog_uuid).pack()
                )
            ], [InlineKeyboardButton(
                text=BaseTexts.BACK,
                callback_data=MistakesListCallback().pack()
            )]]
        )

    @staticmethod
    def mistake(type_key: str, mistake_id: int):
        btn_back = BaseKeyboards.create_btn_back(
            callback_data=MistakeGroupListCallback(group=type_key).pack()
        )
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=MistakesTexts.DELETE_BUTTON, callback_data=DeleteMistakeCallback(pre=True, mistake_id=mistake_id).pack()
            )],
            [btn_back]
        ])

    @staticmethod
    def delete_mistake(mistake_id: int):
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=MistakesTexts.I_WORKED_OUT_MISTAKE_REASON_DELETE_BUTTON,
                callback_data=DeleteMistakeCallback(
                    pre=False, mistake_id=mistake_id,
                    is_worked_out=True
                ).pack()
            )],
            [InlineKeyboardButton(
                text=MistakesTexts.ERROR_MISTAKE_REASON_DELETE_BUTTON,
                callback_data=DeleteMistakeCallback(
                    pre=False, mistake_id=mistake_id,
                    really_delete=True
                ).pack()
            )],
            [BaseKeyboards.create_btn_back(MistakeCallback(id=mistake_id).pack())]
        ])


    @staticmethod
    def train_mistake_choice(choices: list[ResChoice], mistake_id: int, group: str) -> InlineKeyboardMarkup:
        btns = BaseKeyboards.create_list_kb(
            get_btn=lambda x: InlineKeyboardButton(
                text=str(x.id) + '️⃣ ',
                callback_data=TrainMistakeGroupAnswerCallback(
                    is_right=x.is_right, mistake_id=mistake_id,
                    group=group
                ).pack()
            ),
            objs=choices,
            width=4
        )
        return InlineKeyboardMarkup(inline_keyboard=btns + [[InlineKeyboardButton(
            text=MistakesTexts.EXIT_BUTTON, callback_data=MistakeGroupListCallback(group=group).pack()
        )]])