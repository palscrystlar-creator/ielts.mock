import os
import tempfile
import logging

from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import CommandStart

from . import ai

logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        f"Salom, {message.from_user.first_name}! 👋\n\n"
        "Menga xohlagan narsangizni yozing yoki ovozli xabar yuboring.\n"
        "• O'zbekcha yozsangiz — bemalol suhbatlashamiz.\n"
        "• Inglizcha yozsangiz/gapirsangiz — IELTS xatolaringizni ayovsiz tekshirib beraman!"
    )


@router.message(F.voice)
async def handle_voice(message: Message):
    await message.bot.send_chat_action(chat_id=message.chat.id, action="record_voice")

    with tempfile.TemporaryDirectory() as tmp:
        ogg_path = os.path.join(tmp, "voice.ogg")
        try:
            file = await message.bot.get_file(message.voice.file_id)
            await message.bot.download_file(file.file_path, ogg_path)
            text = ai.transcribe_audio(ogg_path)
        except Exception as e:
            logger.exception("Voice error")
            await message.answer("❌ Audioni eshitishda xatolik yuz berdi.")
            return

        try:
            response = ai.smart_reply(text)
            await message.answer(f"📝 <i>Eshitganim: {text}</i>\n\n{response}")

            # Ovozli javob faylini yaratish va yuborish
            mp3_path = os.path.join(tmp, "reply.mp3")
            ai.text_to_speech(response, mp3_path)
            await message.answer_voice(FSInputFile(mp3_path))
        except Exception as e:
            logger.exception("AI Response error")
            await message.answer("❌ Javob tayyorlashda xatolik bo'ldi.")


@router.message(F.text & ~F.text.startswith("/"))
async def handle_text(message: Message):
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    try:
        response = ai.smart_reply(message.text)
        await message.answer(response)
    except Exception as e:
        logger.exception("Text error")
        await message.answer("❌ Nimadir xato ketdi, qayta urinib ko'ring.")
