from aiogram import Router, F
from aiogram.types import CallbackQuery
from bot.keyboards.ref import RefKeyboards
from bot.middlewares import DatabaseMiddleware
from bot.texts.ref import RefTexts
from config import settings
from services.ref_service import RefService
from services.users_service import UsersService
from sqlalchemy.ext.asyncio import AsyncSession
from bot.keyboards.base import BaseKeyboards

router = Router()
router.callback_query.middleware(DatabaseMiddleware())


@router.callback_query(F.data == 'ref')
async def ref(
    call: CallbackQuery, db: AsyncSession
):
    ref_info = await RefService(db).get_user_ref_info(user_tid=call.from_user.id, bot=call.bot)
    if ref_info.paid_refs_percent:
        text = RefTexts.special_main(
            ref_link=ref_info.ref_link,
            balance=ref_info.paid_refs_balance,
            percent=ref_info.paid_refs_percent,
            paid_refs=ref_info.count_paid_refs
        )
        is_special = True
    else:
        text = RefTexts.main(
            credits_for_ref=ref_info.credits_for_ref,
            credits_for_paid_ref=ref_info.credits_for_paid_ref,
            ref_link=ref_info.ref_link,
            count_refs=ref_info.count_refs,
            count_paid_refs=ref_info.count_paid_refs,
            got_credits_from_refs=ref_info.got_credits_from_refs
        )
        is_special = False

    await call.message.edit_text(
        text, reply_markup=RefKeyboards.main(is_special=is_special)
    )


@router.callback_query(F.data == 'about-special-ref')
async def about_special_ref(
    call: CallbackQuery, db: AsyncSession
):
    special_ref_on_moderation = await UsersService(db).get_special_ref_on_moderation(call.from_user.id)
    await call.message.edit_text(
        RefTexts.about_special_ref(on_moderation=special_ref_on_moderation),
        reply_markup=RefKeyboards.about_special_ref(on_moderation=special_ref_on_moderation)
    )


@router.callback_query(F.data == 'special-ref-submit-request')
async def special_ref_submit_request(
    call: CallbackQuery, db: AsyncSession
):
    await call.bot.send_message(
        chat_id=settings.ADMIN_ID,
        text=RefTexts.on_submit_request_special_ref(
            user_id=call.from_user.id,
            username=call.from_user.username,
            full_name=call.from_user.full_name
        )
    )
    await call.answer('Заявка подана', show_alert=True)
    await call.message.delete_reply_markup()

    await UsersService(db).switch_special_ref_on_moderation(user_tid=call.from_user.id, value=True)

    await ref(call, db)