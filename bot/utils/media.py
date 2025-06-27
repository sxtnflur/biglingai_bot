import os
from pathlib import Path

from aiogram.types import Voice
from config import settings


async def save_voice_as_mp3(voice: Voice) -> str:
    """Скачивает голосовое сообщение и сохраняет в формате mp3."""
    if not os.path.exists(f"{settings.BASE_DIR}/files"):
        os.mkdir(f"{settings.BASE_DIR}/files")

    voice_mp3_path = f"{settings.BASE_DIR}/files/voice-{voice.file_unique_id}.mp3"
    voice_file_info = await voice.bot.get_file(voice.file_id)
    await voice.bot.download_file(file_path=voice_file_info.file_path, destination=Path(voice_mp3_path))
    return voice_mp3_path