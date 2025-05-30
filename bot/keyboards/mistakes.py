from uuid import UUID

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from schemas.chatting import MistakeSubGroup
from services.ai.base import Choice
from services.mistakes_service import MistakeSchema, MistakeGroupSchema
from .base import BaseKeyboards
from ..callbacks.mistakes import MistakesListCallback, MistakesListByDialogCallback, MistakeCallback, \
    MistakeGroupListCallback, TrainMistakeGroupAnswerCallback, TrainMistakeGroupCallback, TrainMistakesDialogCallback
import textwrap


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
                text='{} ({})'.format(m.group.subgroup_label, m.count_mistakes),
                callback_data=MistakeGroupListCallback(group=m.group.value).pack()
            ),
            limit=limit, objs=groups,
            additional_btns=[[InlineKeyboardButton(text='Назад', callback_data='start')]]
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
                    text='Отработать ошибки',
                    callback_data=MistakesListCallback().pack()  # MistakesListByDialogCallback(dialog_uuid=dialog_uuid.__str__()).pack()
                )],
                [InlineKeyboardButton(
                    text='Начать новый диалог',
                    callback_data='chatting_mode_start'
                )]
            ])
        else:
            return InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text='Начать новый диалог',
                    callback_data='chatting_mode_start'
                )]
            ])

    @staticmethod
    def mistakes_list(
        mistakes: list[MistakeSchema],
        page: int,
        limit: int,
        group: MistakeSubGroup
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
            pag_btn_additional_kwargs=dict(group=group.value),
            additional_btns=[[
                InlineKeyboardButton(
                    text='Отработать ошибки',
                    callback_data=TrainMistakeGroupCallback(group=group.value).pack()
                )
            ], [InlineKeyboardButton(
                text='Назад',
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
                    text='Отработать ошибки',
                    callback_data=TrainMistakesDialogCallback(dialog_uuid=dialog_uuid).pack()
                )
            ], [InlineKeyboardButton(
                text='Назад',
                callback_data=MistakesListCallback().pack()
            )]]
        )

    @staticmethod
    def mistake(group: MistakeSubGroup):
        return BaseKeyboards.create_kb_back(
            callback_data=MistakeGroupListCallback(group=group.value).pack()
        )

    @staticmethod
    def train_mistake_choice(choices: list[Choice], mistake_id: int, group: MistakeSubGroup) -> InlineKeyboardMarkup:
        btns = BaseKeyboards.create_list_kb(
            get_btn=lambda x: InlineKeyboardButton(
                text=x.text,
                callback_data=TrainMistakeGroupAnswerCallback(
                    is_right=x.is_right, mistake_id=mistake_id,
                    group=group.value
                ).pack()
            ),
            objs=choices,
            width=2
        )
        return InlineKeyboardMarkup(inline_keyboard=btns + [[InlineKeyboardButton(
            text='Выйти', callback_data=MistakeGroupListCallback(group=group.value).pack()
        )]])