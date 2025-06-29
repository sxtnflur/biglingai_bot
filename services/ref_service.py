import re

from aiogram import Bot
from aiogram.utils.deep_linking import create_start_link
from bot.keyboards.ref import RefKeyboards
from bot.texts.ref import RefTexts
from database import models
from schemas.ref import UserRefInfo, DecodedRefInfo
from sqlalchemy import select, func, exists, update, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, load_only
from schemas.users import User as UserSchema
from typing_extensions import Literal
from .subs_service import SubsService, SubsServiceProtocol
from .users_service import UsersService

class RefService:
    def __init__(self, subs_service: SubsServiceProtocol):
        self.subs_service = subs_service

    async def create_ref_link(self, user_tid: int, bot: Bot):
        return await create_start_link(
            bot=bot, payload='ref{}'.format(user_tid)
        )

    async def process_ref_payload(self, payload: str, user_id: int, db: AsyncSession) -> DecodedRefInfo | None:
        try:
            ref_user_id = None
            if payload.startswith('ref'):
                ref_user_id = payload.split('ref')[-1]

            print(f'{ref_user_id=}')
            if ref_user_id and len(ref_user_id) == 1:
                ref_user_id = int(ref_user_id[0])

                if ref_user_id == user_id:
                    return

                if not await UsersService(db).check_if_user_exists(ref_user_id):
                    return
                return DecodedRefInfo(invited_by_id=ref_user_id)
        except:
            return

    async def on_user_paid(self, db: AsyncSession, user_tid: int, amount: int, sub_id: int, bot: Bot) -> None:
        has_payments = await db.scalar(
            select(exists().where(models.Payment.user_id == user_tid))
        )
        if has_payments:
            return

        Refferal = aliased(models.User)
        refferer = await db.scalar(
            select(models.User)
            .filter(
                Refferal.invited_by_id.is_not(None),
                Refferal.invited_by_id == models.User.id,
                Refferal.id == user_tid
            )
        )

        if not refferer:
            return

        stmt = (
            update(models.User)
            .filter(
                Refferal.invited_by_id.is_not(None),
                Refferal.invited_by_id == models.User.id,
                Refferal.id == user_tid
            )
        )

        refferer = UserSchema.model_validate(refferer)

        if refferer.paid_refs_percent:
            stmt = (
                stmt.values(
                    paid_refs_balance=case(
                        (models.User.paid_refs_percent.is_(None), models.User.paid_refs_balance),
                        else_=func.coalesce(models.User.paid_refs_balance, 0) + (
                                (amount * func.coalesce(models.User.paid_refs_percent, 0)) // 100
                        ))
                ).returning(
                    models.User.paid_refs_balance,
                    ((amount * models.User.paid_refs_percent) // 100)
                )
            )
            res = await db.execute(stmt)
            if not res:
                return
            res = res.fetchone()
            if not res:
                return

            all_balance, add_balance = res

            await bot.send_message(
                refferer.id,
                text=RefTexts.ref_special_ref_paid_notification(
                    full_name=refferer.full_name,
                    username=refferer.username,
                    add_balance=add_balance,
                    all_balance=all_balance
                ),
                reply_markup=RefKeyboards.on_ref_event()
            )
        else:
            sub = await self.subs_service.get_sub(sub_id, db=db)
            increase_days = sub.days // 2
            sub_end = await self.subs_service.create_or_increase_sub_by_days(
                days=increase_days, user_id=user_tid, db=db
            )
            await bot.send_message(
                refferer.id,
                text=RefTexts.ref_paid_notification(
                    full_name=refferer.full_name,
                    username=refferer.username,
                    days=increase_days,
                    sub_end=sub_end
                ),
                reply_markup=RefKeyboards.on_ref_event()
            )

    async def get_user_ref_info(
            self, db: AsyncSession, user_tid: int, bot: Bot
    ) -> UserRefInfo:
        ref_link = await self.create_ref_link(user_tid, bot)

        stmt_count_refs = (
            select(
                func.count(),
                func.count(
                    expression=exists().where(models.Payment.user_id == models.User.id)
                ))
            .filter(models.User.invited_by_id == user_tid, models.User.id != user_tid)
        )
        count_refs, count_paid_refs = (await db.execute(stmt_count_refs)).fetchone()
        user: models.User = await db.scalar(
            select(models.User)
            .options(
                load_only(
                    models.User.id,
                    models.User.paid_refs_balance,
                    models.User.paid_refs_percent,
                    models.User.credits_from_refs,
                    models.User.special_ref_on_moderation
                )
            )
            .filter(models.User.id == user_tid)
        )
        return UserRefInfo(
            ref_link=ref_link,
            count_refs=count_refs,
            count_paid_refs=count_paid_refs,
            paid_refs_percent=user.paid_refs_percent,
            paid_refs_balance=user.paid_refs_balance,
            special_ref_on_moderation=user.special_ref_on_moderation
        )
