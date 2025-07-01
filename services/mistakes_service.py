from uuid import UUID

from pydantic import BaseModel
from schemas.chatting import MistakeSubGroup, Mistake as MistakeRes, GroupEnum, MistakeType
from sqlalchemy import insert, select, func, text, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from database import models
from sqlalchemy.orm import selectinload


class MistakeSchema(BaseModel):
    id: int
    type: MistakeType
    explanation: str
    incorrect: str
    correct: str
    example: list[str]

    user_id: int
    dialog_uuid: UUID
    user_message: str

    class Config:
        from_attributes = True


class MistakeSchemaNoType(BaseModel):
    id: int
    type_key: str
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
    type: MistakeType
    count_mistakes: int


class MistakesService:
    def __init__(self, db: AsyncSession) -> None:
        self.__db = db

    async def save_mistake(
            self, user_id: int, mistake_subgroup: MistakeSubGroup, comment: str, dialog_uuid: UUID,
            user_message: str
    ) -> MistakeSchema:
        stmt = (
            insert(models.Mistake)
            .values(
                user_id=user_id, group=mistake_subgroup,
                comment=comment, dialog_uuid=dialog_uuid,
                user_message=user_message
            )
            .returning(models.Mistake.id)
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
            type_key=mistake.type,
            explanation=mistake.explanation,
            incorrect=mistake.incorrect,
            correct=mistake.correct,
            example=mistake.example,
            user_message=user_message
        ) for mistake in mistakes]
        stmt = (
            insert(models.Mistake)
            .values(values)
        )
        await self.__db.execute(stmt)

    async def add_mistake_group_if_not_exists(
        self, key: str, name: str
    ) -> str:
        stmt = text('''
        INSERT INTO mistake_types (key, name)
        VALUES (:key, :name)
        ON CONFLICT (key) DO NOTHING
        RETURNING name
        ''').bindparams(key=key, name=name)
        return await self.__db.scalar(stmt)

    async def add_mistake_groups_if_not_exist(self, groups: list[dict]) -> list[dict]:
        res = []
        for group in groups:
            group_name = await self.add_mistake_group_if_not_exists(key=group['key'], name=group['name'])
            res.append({'key': group['key'], 'name': group_name})
        return res

    async def get_mistakes(
        self,
        user_id: int,
        by_type_key: str | None = None,
        by_dialog_uuid: UUID | None = None,
        offset: int = 0,
        limit: int = 10
    ) -> list[MistakeSchema]:
        stmt = (
            select(models.Mistake)
            .filter(models.Mistake.user_id == user_id, models.Mistake.is_worked_out.is_(False))
            .options(selectinload(models.Mistake.type))
            .offset(offset).limit(limit)
            .order_by(models.Mistake.id)
        )
        if by_type_key:
            stmt = stmt.filter(models.Mistake.type_key == by_type_key)
        if by_dialog_uuid:
            stmt = stmt.filter(models.Mistake.dialog_uuid == by_dialog_uuid)
        mistakes = await self.__db.scalars(stmt)
        return list(map(MistakeSchema.model_validate, mistakes))

    async def get_user_mistake_groups(
        self,
        user_id: int,
        offset: int = 0,
        limit: int = 10
    ) -> list[MistakeGroupSchema]:
        stmt = (
            select(models.MistakeType, func.count().label('count'))
            .join(models.Mistake, models.Mistake.type_key == models.MistakeType.key)
            .filter(models.Mistake.user_id == user_id, models.Mistake.is_worked_out.is_(False))
            .offset(offset).limit(limit)
            .group_by(models.MistakeType.key)
            .order_by(text('count'))
        )
        groups = (await self.__db.execute(stmt)).fetchall()
        if not groups:
            return []
        return list(map(
            lambda x: MistakeGroupSchema(type=x[0], count_mistakes=x[1]),
            groups
        ))

    async def get_mistake(
        self, mistake_id: int
    ) -> MistakeSchema:
        stmt = (
            select(models.Mistake)
            .options(selectinload(models.Mistake.type))
            .filter(models.Mistake.id == mistake_id)
        )
        obj = await self.__db.scalar(stmt)
        return MistakeSchema.model_validate(obj)

    async def get_random_mistake(
        self, user_id: int,
        by_type_key: str | None = None,
        by_dialog_uuid: str | UUID | None = None
    ) -> MistakeSchema | None:
        stmt = (
            select(models.Mistake)
            .options(selectinload(models.Mistake.type))
            .filter(models.Mistake.user_id == user_id,
                    models.Mistake.is_worked_out.is_(False))
        )
        if by_type_key:
            stmt = stmt.filter(models.Mistake.type_key == by_type_key)
        if by_dialog_uuid:
            if isinstance(by_dialog_uuid, str):
                by_dialog_uuid = UUID(by_dialog_uuid)
            stmt = stmt.filter(models.Mistake.dialog_uuid == by_dialog_uuid)

        stmt = stmt.order_by(func.random()).limit(1)
        obj = await self.__db.scalar(stmt)
        if not obj:
            return
        return MistakeSchema.model_validate(obj)

    async def delete_mistake(self, mistake_id: int, user_id: int) -> MistakeSchemaNoType:
        mistake = await self.__db.scalar(
            delete(models.Mistake).filter(models.Mistake.id == mistake_id, models.Mistake.user_id == user_id)
            .returning(models.Mistake)
        )
        return MistakeSchemaNoType.model_validate(mistake)

    async def mark_mistake_as_worked_out(self, mistake_id: int, user_id: int) -> MistakeSchemaNoType:
        mistake = await self.__db.scalar(
            update(models.Mistake)
            .filter(models.Mistake.id == mistake_id,  models.Mistake.user_id == user_id)
            .values(is_worked_out=True)
            .returning(models.Mistake)
        )
        return MistakeSchemaNoType.model_validate(mistake)

    async def count_worked_out_mistakes(self, user_id: int) -> int:
        return await self.__db.scalar(
            select(func.count())
            .filter(
                models.Mistake.user_id == user_id,
                models.Mistake.is_worked_out.is_(True)
            )
        )