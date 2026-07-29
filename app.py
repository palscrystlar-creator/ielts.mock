import os
import logging
import tempfile
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Update

from bot.handlers import router
from bot import ai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable topilmadi (.env faylni tekshiring)")

# Render avtomatik RENDER_EXTERNAL_URL beradi, lokal uchun BASE_URL ishlatiladi
BASE_URL = os.getenv("RENDER_EXTERNAL_URL") or os.getenv("BASE_URL")
WEBHOOK_PATH = "/webhook"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
dp.include_router(router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if BASE_URL:
        webhook_url = f"{BASE_URL.rstrip('/')}{WEBHOOK_PATH}"
        await bot.set_webhook(webhook_url, drop_pending_updates=True)
        logger.info(f"Webhook o'rnatildi: {webhook_url}")
    else:
        logger.warning("BASE_URL/RENDER_EXTERNAL_URL topilmadi — webhook o'rnatilmadi (lokal test rejimi).")
    yield
    await bot.session.close()


app = FastAPI(lifespan=lifespan)

# Mini App statik fayllarini /miniapp/ manzilida ko'rsatish
app.mount("/miniapp", StaticFiles(directory="miniapp", html=True), name="miniapp")


@app.get("/")
async def root():
    return {"status": "ok", "service": "IELTS Speaking Telegram Bot"}


@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.model_validate(data, context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}


# =========================================================
#  Mini App API — IELTS Mock Test
# =========================================================

# Sodda xotira-ichi sessiya (shaxsiy/test foydalanish uchun yetarli)
SESSIONS: dict[str, dict] = {}

# Mock test tuzilishi: 2 ta Part1, 1 ta Part2 (cue card), 2 ta Part3
PART_ORDER = ["part1", "part1", "part2", "part3", "part3"]


@app.post("/api/mock/start")
async def mock_start(user_id: str = Form(...)):
    question = ai.generate_question("part1")
    SESSIONS[user_id] = {"step": 0, "current_question": question, "history": []}
    return {
        "question": question,
        "part": "part1",
        "step": 0,
        "total": len(PART_ORDER),
    }


@app.post("/api/mock/answer")
async def mock_answer(user_id: str = Form(...), audio: UploadFile = File(...)):
    session = SESSIONS.get(user_id)
    if not session:
        return JSONResponse(
            {"error": "Sessiya topilmadi. Iltimos, testni qaytadan boshlang."}, status_code=400
        )

    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
        tmp.write(await audio.read())
        tmp_path = tmp.name

    try:
        answer_text = ai.transcribe_audio(tmp_path)
    except Exception as e:
        logger.exception("Mock transcribe error")
        return JSONResponse({"error": f"Audio tahlilida xatolik: {e}"}, status_code=500)
    finally:
        os.remove(tmp_path)

    part = PART_ORDER[session["step"]]

    try:
        evaluation = ai.evaluate_answer(session["current_question"], answer_text, part)
    except Exception as e:
        logger.exception("Mock evaluate error")
        return JSONResponse({"error": f"Baholashda xatolik: {e}"}, status_code=500)

    session["history"].append(
        {"question": session["current_question"], "answer": answer_text, "eval": evaluation}
    )
    session["step"] += 1

    if session["step"] >= len(PART_ORDER):
        try:
            report = ai.final_report(session["history"])
        except Exception as e:
            logger.exception("Final report error")
            report = None
        del SESSIONS[user_id]
        return {
            "finished": True,
            "answer_text": answer_text,
            "evaluation": evaluation,
            "final_report": report,
        }

    next_part = PART_ORDER[session["step"]]
    try:
        next_question = ai.generate_question(next_part)
    except Exception as e:
        logger.exception("Next question error")
        return JSONResponse({"error": f"Keyingi savol yaratishda xatolik: {e}"}, status_code=500)

    session["current_question"] = next_question

    return {
        "finished": False,
        "answer_text": answer_text,
        "evaluation": evaluation,
        "next_question": next_question,
        "part": next_part,
        "step": session["step"],
        "total": len(PART_ORDER),
    }


@app.post("/api/tts")
async def api_tts(text: str = Form(...)):
    """Berilgan matnni ovozga aylantirib, mp3 fayl sifatida qaytaradi."""
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        path = tmp.name
    try:
        ai.text_to_speech(text[:1000], path)
    except Exception as e:
        logger.exception("TTS API error")
        return JSONResponse({"error": f"Ovoz yaratishda xatolik: {e}"}, status_code=500)
    return FileResponse(path, media_type="audio/mpeg", filename="speech.mp3")
