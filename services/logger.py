from aiogram import Bot


class LoggerService:
    def __init__(self, admin_tg_ids: list[int], bot_token: str):
        self.admin_tg_ids = admin_tg_ids
        self.bot = Bot(token=bot_token)

    async def log_by_telegram_bot(self, message: str, only_admin_ids: list[int] | None = None):
        admin_ids = only_admin_ids or self.admin_tg_ids
        for admin_id in admin_ids:
            await self.bot.send_message(chat_id=admin_id, text=message)