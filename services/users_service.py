from datetime import timedelta, datetime

from config import settings
from database.models import User
from exceptions import CreditsOverException
from sqlalchemy import text, select, update, exists, func, case, or_
from sqlalchemy.exc import DatabaseError
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.types import User as TgUser
from typing_extensions import Literal
from schemas.users import User as UserSchema


class UsersService:
    def __init__(self, db: AsyncSession) -> None:
        self.__db = db

    async def add_user(
        self, user_tid: int, username: str | None, first_name: str,
        last_name: str | None,
        invited_by_id: int | None = None,
        start_credits: int = settings.START_CREDITS
    ) -> UserSchema | None:
        stmt = text('''
INSERT INTO users (id, username, first_name, last_name, credits, invited_by_id)
VALUES (:user_id, :username, :first_name, :last_name, :start_credits, :invited_by_id)
ON CONFLICT (id) DO UPDATE SET
username = EXCLUDED.username,
first_name = EXCLUDED.first_name,
last_name = EXCLUDED.last_name,
updated_at = now()
RETURNING credits, sub_end
''').bindparams(
            user_id=user_tid, username=username,
            first_name=first_name, last_name=last_name,
            start_credits=start_credits,
            invited_by_id=invited_by_id
        )
        res = await self.__db.execute(stmt)
        if not res:
            return
        res = res.fetchone()
        if not res:
            return
        return UserSchema(
            id=user_tid, username=username,
            first_name=first_name, last_name=last_name,
            credits=res[0], sub_end=res[1]
        )

    async def add_user_from_tguser(self, user: TgUser, invited_by_id: int | None = None,
                                   start_credits: int = settings.START_CREDITS) -> UserSchema:
        res = await self.add_user(
            user_tid=user.id, username=user.username,
            first_name=user.first_name, last_name=user.last_name,
            invited_by_id=invited_by_id, start_credits=start_credits
        )
        return res

    async def get_user_credits(self, user_tid: int) -> int | None:
        return await self.__db.scalar(
            select(User.credits).filter(User.id == user_tid)
        )

    async def get_user(self, user_tid: int) -> UserSchema:
        user = await self.__db.scalar(
            select(User).filter(User.id == user_tid)
        )
        return UserSchema.model_validate(user)

    async def update_user_credits(self, user_tid: int, credits: int, action: Literal['up', 'down']) -> int:
        if action == 'down' and (not await self.get_user_credits(user_tid)):
            raise CreditsOverException
        stmt = (
            update(User)
            .filter(User.id == user_tid)
        )
        if action == 'up':
            stmt = stmt.values(credits=User.credits + credits)
        elif action == 'down':
            stmt = stmt.values(credits=User.credits - credits)
        else:
            raise
        try:
            return await self.__db.scalar(stmt.returning(User.credits))
        except DatabaseError:
            raise CreditsOverException

    async def do_paid_action(self, user_tid: int, credits: int = 1) -> bool:
        has_sub = await self.__db.scalar(
            select(exists().where(
                User.id == user_tid,
                User.sub_end.is_not(None),
                User.sub_end > func.now()
            ))
        )
        if has_sub:
            return True

        try:
            await self.update_user_credits(
                user_tid, credits, action='down'
            )
        except CreditsOverException:
            return False
        else:
            return True

    async def check_access_to_paid_action(self, user_tid: int, credits: int) -> bool:
        has_sub = await self.__db.scalar(
            select(exists().where(
                User.id == user_tid,
                User.sub_end.is_not(None),
                User.sub_end > func.now()
            ))
        )
        if has_sub:
            return True

        user_credits = await self.get_user_credits(user_tid)
        return user_credits >= credits

    async def give_sub(self, user_tid: int, td: timedelta) -> datetime:
        stmt = (
            update(User)
            .filter(User.id == user_tid)
            .values(sub_end=case(
                (or_(User.sub_end.is_(None), User.sub_end < func.now()), func.now()),
                else_=User.sub_end
            ) + td)
            .returning(User.sub_end)
        )
        return await self.__db.scalar(stmt)

    async def switch_special_ref_on_moderation(self, user_tid: int, value: bool = True) -> None:
        stmt = (
            update(User).filter(User.id == user_tid)
            .values(special_ref_on_moderation=value)
        )
        await self.__db.execute(stmt)

    async def get_special_ref_on_moderation(self, user_tid: int) -> bool:
        return await self.__db.scalar(
            select(User.special_ref_on_moderation).filter(User.id == user_tid)
        )