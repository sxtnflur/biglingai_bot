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


@router.message(F.text)
async def get_word(
        msg: Message
):
    text = DictionaryTexts.what_do_with_your_text(msg.text)

    translate_index_from = text.find('<blockquote>') + len('<blockquote>')
    translate_index_to = text.find('</blockquote>')
    await msg.answer(
        text=DictionaryTexts.what_do_with_your_text(msg.text),
        reply_markup=DictionaryKeyboards.do_action_with_word(
            msg.text, (translate_index_from, translate_index_to)
        )
    )


router_ = Router()
router.include_router(router_)
router_.message.middleware(DatabaseMiddleware())


@router_.message(F.reply_to_message.text | F.reply_to_message.caption)
async def add_to_dict_replied_word(
        msg: Message, db: AsyncSession
):
    replied_message_text = msg.reply_to_message.text or msg.reply_to_message.caption
    print(f'{replied_message_text=}')
    print(f'{msg.text=}')
    if msg.text == 'В словарь':
        if len(msg.text.split()) > 1:
            await msg.answer(
                'В словарь можно добавить только одно слово, а вы ввели несколько:\n\n'
                '<blockquote>{}</blockquote>'.format(replied_message_text)
            )
            return
        await dictionary_service.join_or_generate_word(
            word=replied_message_text, user_id=msg.from_user.id, db=db
        )
        await msg.answer('Слово {} добавлено в словарь!'.format(replied_message_text))

    elif msg.text == 'Переведи':
        await translator.translate(text=replied_message_text)

    else:
        text = DictionaryTexts.what_do_with_your_text(replied_message_text)

        translate_index_from = text.find('<blockquote>') + len('<blockquote>')
        translate_index_to = text.find('</blockquote>')
        print(text[translate_index_from:translate_index_to])
        await msg.answer(
            text=DictionaryTexts.what_do_with_your_text(replied_message_text),
            reply_markup=DictionaryKeyboards.do_action_with_word(
                replied_message_text, (translate_index_from, translate_index_to)
            )
        )
