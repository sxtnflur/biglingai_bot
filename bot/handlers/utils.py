from aiogram import Router, F
from aiogram.types import CallbackQuery


router = Router()


@router.callback_query(F.data == 'delete-this-message')
async def delete_this_message(call: CallbackQuery):
    await call.answer(text='Сообщение удалено')
    await call.message.delete()


