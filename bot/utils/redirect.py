import aiogram
from aiogram.types import Message
from bot.handlers.dictionary import start_dictionary_message
from bot.handlers.mistakes import mistakes_list
from bot.handlers.ref import ref_message
from bot.handlers.sub import subs_message
from bot.keyboards.base import BaseKeyboards
from bot.keyboards.chatting import ChattingKeyboards
from bot.keyboards.subs import SubsKeyboards
from bot.texts.chatting import ChattingTexts
from bot.texts.subs import SubsTexts
from bot.texts.translation import TranslationTexts
from enums import ChattingMessageType


async def redirect_to_screen(args: str, message: Message):
    if not args.startswith('screen-'):
        return False
    screen = args.split('-')[1]
    match screen:
        case 'chatting':
            await message.answer(
                text=ChattingTexts.START,
                reply_markup=ChattingKeyboards.start(
                    current_message_type=ChattingMessageType.text_and_voice
                )
            )
            return True
        case 'mistakes':
            await mistakes_list(message)
            return True
        case 'dictionary':
            await start_dictionary_message(message)
            return True
        case 'sub':
            await subs_message(message)
            return True
        case 'translator':
            await message.answer(
                TranslationTexts.MAIN,
                reply_markup=BaseKeyboards.create_kb_back('start')
            )
            return True
        case 'ref':
            await ref_message(message)
            return True
    return False