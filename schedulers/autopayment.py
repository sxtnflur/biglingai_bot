from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database import models
from database.init_db import async_session
from sqlalchemy import select, update, func
from sqlalchemy.orm import load_only
from apscheduler.triggers.cron import CronTrigger


def get_job_id(user_id: int):
    return f'autopayment-{user_id}'


class AutopaymentScheduler:
    def __init__(self, scheduler: AsyncIOScheduler, payment_factory, logger_service):
        self.scheduler = scheduler
        self.payment_factory = payment_factory
        self.logger = logger_service

    async def do_pay(self, user_id: int):
        try:
            async with async_session() as session:
                payment_method_id = await session.scalar(
                    update(models.User)
                    .filter(models.User.id == user_id,
                            models.User.payment_method_id.isnot(None),
                            models.User.is_autopayment.is_(True),
                            models.User.autopayment_duration.isnot(None))
                    .values(
                        sub_end=func.coalesce(models.User.sub_end, func.now()) + models.User.autopayment_duration
                    )
                    .returning(models.User.payment_method_id)
                )
                if not payment_method_id:
                    self.scheduler.remove_job(get_job_id(user_id))
                    await session.rollback()
                    await self.logger.log_by_telegram_bot(
                        f'Автооплата для пользователя {user_id} не прошла и дальнейшие автооплаты отменены, '
                        f'так как у пользователя нет payment_method_id/is_autopayment/autopayment_duration'
                    )
                else:
                    await self.payment_factory.create_payment(
                        payment_method='yookassa',
                        payment_method_id=payment_method_id,
                        description='Автооплата',
                        save_payment_method_id=False
                    )
                    await session.commit()
        except Exception as e:
            await self.logger.log_by_telegram_bot(
                f'Автооплата для пользователя {user_id} не прошла из-за ошибки: {e}'
            )
        else:
            await self.logger.log_by_telegram_bot(
                f'Автооплата для пользователя {user_id} успешно произведена!'
            )

    async def restart_autopayment(self):
        await self.logger.log_by_telegram_bot('Запускаю задачи на автооплаты')
        async with async_session() as session:
            users: list[models.User] = await session.scalars(
                select(models.User)
                .options(
                    load_only(
                        models.User.id, models.User.autopayment_duration,
                        models.User.sub_end
                    )
                )
                .filter(
                    models.User.payment_method_id.isnot(None),
                    models.User.is_autopayment.is_(True),
                    models.User.autopayment_duration.isnot(None)
                )
            )

        for user in users:
            self.scheduler.add_job(
                self.do_pay,
                trigger=CronTrigger(
                    year=user.sub_end.year,
                    month=user.sub_end.month,
                    day=user.sub_end.day,
                    hour=user.sub_end.hour,
                    minute=user.sub_end.minute,
                    second=user.sub_end.second
                ),
                id=get_job_id(user.id),
                args=[user.id],
                replace_existing=True
            )

        await self.logger.log_by_telegram_bot('Задачи на автооплаты установлены')