from uuid import UUID

from pydantic import BaseModel
from schemas.chatting import MistakeSubGroup, Mistake as MistakeRes, GroupEnum
from sqlalchemy import insert, select, func, text, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Mistake


class MistakeSchema(BaseModel):
    id: int
    group: GroupEnum
    subgroup: MistakeSubGroup
    explanation: str
    incorrect: str
    correct: str
    example: list[str]

    user_id: int
    dialog_uuid: UUID
    user_message: str

    class Config:
        from_attributes = True


class MistakeGroupSchema(BaseModel):
    group: MistakeSubGroup
    count_mistakes: int


class MistakesService:
    def __init__(self, db: AsyncSession) -> None:
        self.__db = db

    async def save_mistake(
            self, user_id: int, mistake_subgroup: MistakeSubGroup, comment: str, dialog_uuid: UUID,
            user_message: str
    ) -> MistakeSchema:
        stmt = (
            insert(Mistake)
            .values(
                user_id=user_id, group=mistake_subgroup,
                comment=comment, dialog_uuid=dialog_uuid,
                user_message=user_message
            )
            .returning(Mistake.id)
        )
        mistake_id = await self.__db.scalar(stmt)
        return MistakeSchema(
            id=mistake_id,
            user_id=user_id,
            dialog_uuid=dialog_uuid,
            comment=comment,
            group=mistake_subgroup
        )

    async def save_mistakes(
        self,
        user_id: int, dialog_uuid: UUID, mistakes: list[MistakeRes],
        user_message: str
    ) -> None:
        values = [dict(
            user_id=user_id,
            dialog_uuid=dialog_uuid,
            group=mistake.group,
            subgroup=mistake.subgroup,
            explanation=mistake.explanation,
            incorrect=mistake.incorrect,
            correct=mistake.correct,
            example=mistake.example,
            user_message=user_message
        ) for mistake in mistakes]
        stmt = (
            insert(Mistake)
            .values(values)
        )
        await self.__db.execute(stmt)

    async def get_mistakes(
        self,
        user_id: int,
        by_subgroup: MistakeSubGroup | None = None,
        by_dialog_uuid: UUID | None = None,
        offset: int = 0,
        limit: int = 10
    ) -> list[MistakeSchema]:
        stmt = (
            select(Mistake)
            .filter(Mistake.user_id == user_id, Mistake.is_worked_out.is_(False))
            .offset(offset).limit(limit)
            .order_by(Mistake.id)
        )
        if by_subgroup:
            stmt = stmt.filter(Mistake.subgroup == by_subgroup.value)
        if by_dialog_uuid:
            stmt = stmt.filter(Mistake.dialog_uuid == by_dialog_uuid)
        mistakes = await self.__db.scalars(stmt)
        return list(map(MistakeSchema.model_validate, mistakes))

    async def get_user_mistake_groups(
        self,
        user_id: int,
        offset: int = 0,
        limit: int = 10
    ) -> list[MistakeGroupSchema]:
        stmt = (
            select(Mistake.subgroup, func.count().label('count'))
            .filter(Mistake.user_id == user_id, Mistake.is_worked_out.is_(False))
            .offset(offset).limit(limit)
            .group_by(Mistake.subgroup)
            .order_by(text('count'))
        )
        groups = (await self.__db.execute(stmt)).fetchall()
        if not groups:
            return []
        return list(map(
            lambda x: MistakeGroupSchema(group=x[0], count_mistakes=x[1]),
            groups
        ))

    async def get_mistake(
        self, mistake_id: int
    ) -> MistakeSchema:
        stmt = (
            select(Mistake).filter(Mistake.id == mistake_id)
        )
        obj = await self.__db.scalar(stmt)
        return MistakeSchema.model_validate(obj)

    async def get_random_mistake(
        self, user_id: int,
        by_group: MistakeSubGroup | None = None
    ) -> MistakeSchema | None:
        stmt = (
            select(Mistake)
            .filter(Mistake.user_id == user_id,
                    Mistake.is_worked_out.is_(False))
        )
        if by_group:
            stmt = stmt.filter(Mistake.subgroup == by_group.value)

        stmt = stmt.order_by(func.random()).limit(1)
        obj = await self.__db.scalar(stmt)
        if not obj:
            return
        return MistakeSchema.model_validate(obj)

    async def delete_mistake(self, mistake_id: int, user_id: int) -> MistakeSchema:
        mistake = await self.__db.scalar(
            delete(Mistake).filter(Mistake.id == mistake_id, Mistake.user_id == user_id)
            .returning(Mistake)
        )
        return MistakeSchema.model_validate(mistake)

    async def mark_mistake_as_worked_out(self, mistake_id: int, user_id: int) -> MistakeSchema:
        mistake = await self.__db.scalar(
            update(Mistake)
            .filter(Mistake.id == mistake_id, Mistake.user_id == user_id)
            .values(is_worked_out=True)
            .returning(Mistake)
        )
        return MistakeSchema.model_validate(mistake)

    async def count_worked_out_mistakes(self, user_id: int) -> int:
        return await self.__db.scalar(
            select(func.count())
            .filter(
                Mistake.user_id == user_id,
                Mistake.is_worked_out.is_(True)
            )
        )