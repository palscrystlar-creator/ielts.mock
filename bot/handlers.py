import os
import tempfile
import logging

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import CommandStart, Command

from .keyboards import main_menu, assistant_menu
from . import ai

logger = logging.getLogger(__name__)
router = Router()

# Eslatma: bu oddiy xotira-ichi holat, faqat shaxsiy/test foydalanish uchun yetarli.
# Ko'p foydalanuvchi/production uchun buni Redis yoki DB'ga ko'chirish kerak bo'ladi.
USER_MODE: dict[int, str] = {}

WELCOME_TEXT = (
    "Salom! 👋 Men sizning IELTS Speaking yordamchingizman.\n\n"
    "🗣 <b>IELTS Mock Test</b> — alohida oynada ochiladigan, to'liq ovozli mock speaking test. "
    "Har safar AI random savollar tanlaydi.\n\n"
    "💬 <b>AI Assistant</b> — shu yerda, chatda ovozli yoki yozma gapiring. "
    "Xatolaringiz aynan qaysi joyda ekanini tushuntirib, to'g'ri variantini ko'rsataman.\n\n"
    "Boshlash uchun tugmalardan birini tanlang 👇"
)

ASSISTANT_TEXT = (
    "💬 <b>AI Assistant rejimi yoqildi</b>\n\n"
    "Menga ovozli xabar yuboring yoki matn yozing — ingliz tilida gapirishga harakat qiling.\n"
    "Men xatolaringizni aynan qaysi joyda ekanini tushuntirib, to'g'ri variantini ko'rsataman."
)


@router.message(CommandStart())
async def cmd_start(message: Message):
    USER_MODE[message.from_user.id] = "menu"
    await message.answer(WELCOME_TEXT, reply_markup=main_menu())


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "🗣 IELTS Mock — tugmani bosing, mini oynada AI bilan to'liq speaking test topshirasiz.\n"
        "💬 AI Assistant — shu yerda erkin practice qiling, xatolar tushuntiriladi.\n\n"
        "Boshqa menyuga qaytish uchun /start yozing."
    )


@router.callback_query(F.data == "mode_assistant")
async def cb_assistant(callback: CallbackQuery):
    USER_MODE[callback.from_user.id] = "assistant"
    await callback.message.edit_text(ASSISTANT_TEXT, reply_markup=assistant_menu())
    await callback.answer()


@router.callback_query(F.data == "mode_menu")
async def cb_menu(callback: CallbackQuery):
    USER_MODE[callback.from_user.id] = "menu"
    await callback.message.edit_text(WELCOME_TEXT, reply_markup=main_menu())
    await callback.answer()


@router.callback_query(F.data == "help")
async def cb_help(callback: CallbackQuery):
    await callback.answer(
        "IELTS Mock — ovozli mock test (mini oynada).\nAI Assistant — practice va xato tuzatish.",
        show_alert=True,
    )


@router.message(F.voice)
async def handle_voice(message: Message, bot: Bot):
    mode = USER_MODE.get(message.from_user.id, "menu")
    if mode != "assistant":
        await message.answer(
            "Ovozli practice uchun avval 💬 <b>AI Assistant</b> rejimini tanlang: /start bosing."
        )
        return

    processing = await message.answer("🎧 Eshityapman...")

    with tempfile.TemporaryDirectory() as tmp:
        ogg_path = os.path.join(tmp, "voice.ogg")
        try:
            file = await bot.get_file(message.voice.file_id)
            await bot.download_file(file.file_path, ogg_path)
            text = ai.transcribe_audio(ogg_path)
        except Exception as e:
            logger.exception("Voice transcribe error")
            await processing.edit_text(f"❌ Audioni matnga aylantirishda xatolik yuz berdi: {e}")
            return

        await processing.edit_text(f"📝 Eshitganim: <i>{text}</i>\n\n⏳ Tahlil qilyapman...")

        try:
            feedback = ai.correct_and_explain(text)
        except Exception as e:
            logger.exception("Correction error")
            await message.answer(f"❌ Tahlil qilishda xatolik yuz berdi: {e}")
            return

        await message.answer(feedback)

        try:
            mp3_path = os.path.join(tmp, "reply.mp3")
            ai.text_to_speech(feedback[:900], mp3_path)
            await message.answer_voice(FSInputFile(mp3_path))
        except Exception:
            logger.exception("TTS reply error (ovozsiz javob bilan davom etildi)")


@router.message(F.text & ~F.text.startswith("/"))
async def handle_text(message: Message):
    mode = USER_MODE.get(message.from_user.id, "menu")
    if mode != "assistant":
        await message.answer("Amal tanlash uchun /start bosing.")
        return

    processing = await message.answer("⏳ Tekshiryapman...")
    try:
        feedback = ai.correct_and_explain(message.text)
        await processing.edit_text(feedback)
    except Exception as e:
        logger.exception("Text correction error")
        await processing.edit_text(f"❌ Xatolik yuz berdi: {e}")
