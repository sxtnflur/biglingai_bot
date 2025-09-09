from database.models import Base
from sqlalchemy import delete, select, update, exists
from sqlalchemy.ext.asyncio import AsyncSession
from typing_extensions import TypeVar, Protocol

T = TypeVar('T', bound=Base)


class BaseRepo(Protocol[T]):
    model: type[Base]

    def __init__(self, db: AsyncSession):
        self.db = db

    async def add(self, **vals) -> None:
        self.db.add(self.model(**vals))

    async def get_one(self, **filters) -> T:
        return await self.db.scalar(
            select(self.model)
            .filter_by(**filters)
        )

    async def get_list(self, **filters) -> list[T]:
        return await self.db.scalars(
            select(self.model)
            .filter_by(**filters)
        )

    async def get_one_field(self, field: str, **filters):
        return await self.db.scalar(
            select(getattr(self.model, field))
            .filter_by(**filters)
        )

    async def get_only_fields(self, fields: list[str], **filters) -> tuple:
        fields_ = [getattr(self.model, f) for f in fields]
        res = await self.db.execute(
            select(*fields_).filter_by(**filters)
        )
        return res.fetchone()

    async def update(self, filters: dict, updates: dict) -> None:
        await self.db.execute(
            update(self.model)
            .filter_by(**filters)
            .values(**updates)
        )

    async def delete(self, **filters) -> None:
        await self.db.execute(
            delete(self.model)
            .filter_by(**filters)
        )

    async def exists(self, **filters) -> bool:
        return await self.db.scalar(
            select(
                exists()
                .select_from(self.model)
                .where(
                    *[getattr(self.model, key) == value for key, value in filters.items()]
                )
            )
        )