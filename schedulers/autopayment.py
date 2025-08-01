from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database import models
from database.init_db import async_session
from payments import PaymentData
from services.payments_service import PaymentsServiceProtocol
from sqlalchemy.dialects.postgresql import INTERVAL
from .abc import AutopaymentSchedulerProtocol
from sqlalchemy import select, update, func, Interval, String
from sqlalchemy.orm import load_only, selectinload
from apscheduler.triggers.cron import CronTrigger


def get_job_id(user_id: int):
    return f'autopayment-{user_id}'


class AutopaymentScheduler(AutopaymentSchedulerProtocol):
    def __init__(
            self, scheduler: AsyncIOScheduler,
            payment_factory, logger_service,
            payments_service: PaymentsServiceProtocol
    ):
        self.scheduler = scheduler
        self.payment_factory = payment_factory
        self.logger = logger_service
        self.payments_service = payments_service

    async def do_pay(self, user_id: int):
        try:
            async with async_session() as session:
                # result = await session.execute(
                #     update(models.User)
                #     .filter(models.User.id == user_id,
                #             models.User.payment_method_id.isnot(None),
                #             models.User.is_autopayment.is_(True),
                #             models.User.current_sub_id.isnot(None),
                #             models.Sub.id == models.User.current_sub_id
                #     )
                #     .values(
                #         sub_end=(
                #             func.now() + func.cast(func.cast(models.Sub.days, String) + ' minutes', INTERVAL)
                #         )  # TODO: изменить minutes -> days
                #     )
                #     .returning(models.User.payment_method_id, models.Sub.price,
                #                models.User.current_sub_id, models.User.sub_end)
                # )
                user: models.User | None = await session.scalar(
                    select(models.User)
                    .options(load_only(
                        models.User.payment_method_id,
                        models.User.sub_end,
                        models.User.current_sub_id
                    ),
                        selectinload(models.User.current_sub)
                    )
                    .filter(models.User.id == user_id,
                            models.User.payment_method_id.isnot(None),
                            models.User.is_autopayment.is_(True),
                            models.User.current_sub_id.isnot(None)
                    )
                )

                print(f'{user=}')

                if not user:
                    self.remove_user_job(user_id)
                    await self.logger.log_by_telegram_bot(f'Автооплата отменена для {user_id}, так как user не найден (NULL)')
                    return

                # 2. Явно загружаем подписку, если не загружена
                if not user.current_sub or user.current_sub not in session:
                    raise Exception('Нет подписки')

                # 3. Создаем платеж ВНЕ контекста сессии
                payment_data = {
                    'amount': user.current_sub.price,
                    'payment_method': 'yookassa',
                    'payment_method_id': user.payment_method_id,
                    'description': 'Автооплата'
                }
                print(f'{payment_data=}')
                # if not payment_method_id:
                #     self.remove_user_job(user_id)
                #     await session.rollback()
                #     await self.logger.log_by_telegram_bot(
                #         f'Автооплата для пользователя {user_id} не прошла и дальнейшие автооплаты отменены, '
                #         f'так как у пользователя нет payment_method_id/is_autopayment/autopayment_duration'
                #     )
                # else:
                await session.commit()

                payment_id: str = await self.payment_factory.create_auto_payment(**payment_data)
                print(f'{payment_id=}')

                async with session.begin():
                    await self.payments_service.save_autopayment(
                        db=session, user_tid=user_id,
                        amount=payment_data['amount'], sub_id=user.current_sub_id,
                        order_id=payment_id,
                        test=True
                    )
                    self.add_job_to_user(
                        user_id, sub_end=user.sub_end
                    )
                    await session.commit()
        except Exception as e:
            # raise e
            await self.logger.log_by_telegram_bot(
                f'Автооплата для пользователя {user_id} не прошла из-за ошибки: {e}'
            )
        else:
            await self.logger.log_by_telegram_bot(
                f'Автооплата для пользователя {user_id} успешно произведена!'
            )

    def remove_user_job(self, user_id: int) -> None:
        self.scheduler.remove_job(get_job_id(user_id))

    def add_job_to_user(self, user_id: int, sub_end: datetime):
        self.scheduler.add_job(
            self.do_pay,
            trigger=CronTrigger(
                year=sub_end.year,
                month=sub_end.month,
                day=sub_end.day,
                hour=sub_end.hour,
                minute=sub_end.minute,
                second=sub_end.second
            ),
            id=get_job_id(user_id),
            args=[user_id],
            replace_existing=True
        )

    async def restart_autopayment(self):
        await self.logger.log_by_telegram_bot('Запускаю задачи на автооплаты')
        async with async_session() as session:
            users: list[models.User] = await session.scalars(
                select(models.User)
                .options(
                    load_only(
                        models.User.id,
                        models.User.sub_end
                    )
                )
                .filter(
                    models.User.payment_method_id.isnot(None),
                    models.User.is_autopayment.is_(True),
                    models.User.current_sub_id.isnot(None),
                    models.User.sub_end.isnot(None)
                )
            )

        for user in users:
            if user.sub_end > datetime.utcnow():
                self.add_job_to_user(user_id=user.id,
                                     sub_end=user.sub_end)  # sub_end=user.sub_end)
            else:
                await self.do_pay(user_id=user.id)

        await self.logger.log_by_telegram_bot('Задачи на автооплаты установлены')
