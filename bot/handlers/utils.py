from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from bot.keyboards.dictionary import DictionaryKeyboards
from bot.middlewares import DatabaseMiddleware
from bot.texts.dictionary import DictionaryTexts
from depends import dictionary_service, translator
from sqlalchemy.ext.asyncio import AsyncSession


router = Router()


@router.callback_query(F.data == 'delete-this-message')
async def delete_this_message(call: CallbackQuery):
    await call.answer(text='Сообщение удалено')
    await call.message.delete()


