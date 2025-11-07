from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from bot.keyboards.base import BaseKeyboards
from bot.middlewares import DatabaseMiddleware
from bot.texts.base import BaseTexts
from config import settings
from depends import subs_service, ref_service
from schemas.ref import DecodedRefInfo
from services.ref_service import RefService
from services.users_service import UsersService
from sqlalchemy.ext.asyncio import AsyncSession

router = Router()
router.message.middleware(DatabaseMiddleware())
router.callback_query.middleware(DatabaseMiddleware())


@router.message(CommandStart(deep_link=True))
async def start_ref(
    message: Message,
    command: CommandObject,
    state: FSMContext,
    db: AsyncSession
):
    ref_info = DecodedRefInfo()
    if not await UsersService(db).check_if_user_exists(message.from_user.id):
        ref_info = await ref_service.process_ref_payload(
            command.args,
            user_id=message.from_user.id,
            db=db
        )
        print(f'{ref_info=}')

    user = await UsersService(db).add_user_from_tguser(
        message.from_user, invited_by_id=ref_info.invited_by_id,
        sale_percent=ref_info.sale_percent,
        start_credits=(settings.START_CREDITS or 0)
    )
    await state.clear()
    await message.answer(BaseTexts.start(),
                         reply_markup=BaseKeyboards.main_menu())


@router.message(CommandStart(deep_link=False))
async def start(
        message: Message, state: FSMContext, db: AsyncSession
):
    user = await UsersService(db).add_user_from_tguser(message.from_user)
    await state.clear()
    await message.answer(BaseTexts.start(),
                         reply_markup=BaseKeyboards.main_menu())


@router.callback_query(F.data == 'start')
async def start_call(
        call: CallbackQuery, state: FSMContext, db: AsyncSession
):
    await state.clear()
    user = await UsersService(db).get_user(call.from_user.id)
    await call.message.delete_reply_markup()
    await call.message.answer(BaseTexts.start(),
                              reply_markup=BaseKeyboards.main_menu())


@router.message(Command('support'))
async def support(m: Message):
    await m.answer(
        'Если возникнут проблемы, обращайтесь сюда:\n@teledeff_support'
    )