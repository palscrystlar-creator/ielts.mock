import os
import logging
import base64
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import CommandStart
from aiogram.types import Update, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from dotenv import load_dotenv
from groq import Groq
from gtts import gTTS

load_dotenv()

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://ielts-mock-6yvx.onrender.com")

# Token mavjud bo'lsagina Bot va Groq ob'yektini yaratamiz
bot = Bot(token=BOT_TOKEN) if BOT_TOKEN else None
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

if not BOT_TOKEN:
    logging.warning("⚠️ OGOHLANTIRISH: BOT_TOKEN topilmadi! Render Environment Variables'ni tekshiring.")

dp = Dispatcher()
router = Router()
app = FastAPI()

SYSTEM_PROMPT = """
You are 'Sara AI', a warm, friendly, and smart English Live Speaking Coach.
You are conducting a 20-minute voice practice session with the user.

Rules:
1. Keep your answers brief, warm, and natural (1-3 sentences max) so it plays quickly via audio.
2. If the user makes a grammar or vocabulary error, gently mention the correction in 1 short phrase before replying.
3. End your responses with a thought-provoking follow-up question to keep the 20-minute conversation flowing naturally.
"""

# === TELEGRAM BOT HANDLER ===

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    miniapp_url = f"{WEBHOOK_URL.rstrip('/')}/miniapp/"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎙 Start 20-Min Voice Session", web_app=WebAppInfo(url=miniapp_url))]
    ])
    await message.answer(
        "👋 **Xush kelibsiz! Men Sara AI Live Coach'man.**\n\n"
        "20 daqiqalik ovozli muloqot seansini boshlash uchun quyidagi tugmani bosing!",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

dp.include_router(router)

# === FASTAPI ROUTELARI ===

@app.on_event("startup")
async def on_startup():
    if bot and WEBHOOK_URL and WEBHOOK_URL.startswith("https://"):
        url = f"{WEBHOOK_URL.rstrip('/')}/webhook"
        try:
            await bot.set_webhook(url)
            logging.info(f"✅ Webhook muvaffaqiyatli o'rnatildi: {url}")
        except Exception as e:
            logging.error(f"❌ Webhook o'rnatishda xatolik: {e}")
    else:
        logging.warning("⚠️ WEBHOOK_URL ko'rsatilmagan yoki 'https://' bilan boshlanmagan!")
@app.post("/webhook")
async def bot_webhook(request: Request):
    if not bot:
        return JSONResponse({"status": "error", "message": "Bot token sozlangan emas!"}, status_code=500)
    data = await request.json()
    update = Update(**data)
    await dp.feed_update(bot, update)
    return {"status": "ok"}

@app.post("/api/chat")
async def chat_api(request: Request):
    try:
        if not groq_client:
            return JSONResponse({"status": "error", "message": "Groq API Key topilmadi!"}, status_code=500)

        body = await request.json()
        user_text = body.get("text", "")
        time_left = body.get("time_left", 1200)
        
        if not user_text:
            return JSONResponse({"status": "error", "message": "Text is required"}, status_code=400)

        prompt_modifier = ""
        if time_left < 60:
            prompt_modifier = " (Note: The 20-minute session is ending right now. Briefly thank the user and wrap up the practice with a warm closing comment.)"

        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT + prompt_modifier},
                {"role": "user", "content": user_text}
            ],
            temperature=0.7,
            max_tokens=250
        )
        ai_reply = completion.choices[0].message.content

        temp_file = "temp_audio.mp3"
        tts = gTTS(text=ai_reply, lang='en', slow=False)
        tts.save(temp_file)

        with open(temp_file, "rb") as audio_file:
            audio_base64 = base64.b64encode(audio_file.read()).decode("utf-8")

        if os.path.exists(temp_file):
            os.remove(temp_file)

        return JSONResponse({
            "status": "success",
            "reply": ai_reply,
            "audio": f"data:audio/mp3;base64,{audio_base64}"
        })
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

# Single-file HTML Mini App
@app.get("/miniapp/", response_class=HTMLResponse)
async def serve_miniapp():
    html_code = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sara AI - 20 Min Live Coach</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                background-color: #0f172a;
                color: #f8fafc;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: space-between;
                height: 100vh;
                margin: 0;
                padding: 16px;
                box-sizing: border-box;
            }
            .header { text-align: center; }
            .header h1 { font-size: 20px; color: #38bdf8; margin: 0; }
            .timer {
                font-size: 16px;
                font-weight: bold;
                background: #1e293b;
                color: #f59e0b;
                padding: 6px 14px;
                border-radius: 20px;
                display: inline-block;
                margin-top: 6px;
                border: 1px solid #334155;
            }
            .chat-container {
                width: 100%;
                max-width: 420px;
                flex-grow: 1;
                overflow-y: auto;
                margin: 15px 0;
                display: flex;
                flex-direction: column;
                gap: 10px;
            }
            .msg { padding: 12px 16px; border-radius: 16px; font-size: 15px; max-width: 82%; line-height: 1.4; }
            .user { background: #0284c7; align-self: flex-end; border-bottom-right-radius: 4px; }
            .ai { background: #334155; align-self: flex-start; border-bottom-left-radius: 4px; border: 1px solid #475569; }

            .controls { display: flex; flex-direction: column; align-items: center; width: 100%; max-width: 420px; gap: 12px; }
            .mic-btn {
                width: 76px; height: 76px; border-radius: 50%; background: #38bdf8;
                border: none; color: #0f172a; font-size: 30px; cursor: pointer;
                box-shadow: 0 0 20px rgba(56, 189, 248, 0.4); transition: all 0.2s;
                display: flex; align-items: center; justify-content: center;
            }
            .mic-btn.recording { background: #ef4444; box-shadow: 0 0 25px rgba(239, 68, 68, 0.6); animation: pulse 1.2s infinite; }
            
            @keyframes pulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.08); }
                100% { transform: scale(1); }
            }

            .input-box { display: flex; width: 100%; gap: 8px; }
            .input-box input {
                flex: 1; padding: 12px 16px; border-radius: 25px; border: 1px solid #334155;
                background: #1e293b; color: white; outline: none;
            }
            .input-box button {
                padding: 12px 20px; border-radius: 25px; border: none; background: #38bdf8;
                color: #0f172a; font-weight: bold; cursor: pointer;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎙 Sara AI Live Speaking</h1>
            <div class="timer" id="timer">⏱ 20:00</div>
        </div>

        <div class="chat-container" id="chat">
            <div class="msg ai">Hello! I'm Sara. We have 20 minutes to practice speaking today. Tap the microphone or write below to start!</div>
        </div>

        <div class="controls">
            <button class="mic-btn" id="micBtn" onclick="toggleSpeech()">🎙</button>
            <div class="input-box">
                <input type="text" id="userInput" placeholder="Type or speak..." onkeypress="handleKey(event)">
                <button onclick="sendText()">Send</button>
            </div>
        </div>

        <script>
            const tg = window.Telegram.WebApp;
            tg.expand();

            const chat = document.getElementById('chat');
            const micBtn = document.getElementById('micBtn');
            const userInput = document.getElementById('userInput');
            const timerDisplay = document.getElementById('timer');

            let timeLeft = 1200;
            let timerInterval = null;

            function startTimer() {
                if (timerInterval) return;
                timerInterval = setInterval(() => {
                    if (timeLeft <= 0) {
                        clearInterval(timerInterval);
                        timerDisplay.innerText = "⏱ Time's up!";
                        alert("20-minute session complete! Great job practicing today.");
                        return;
                    }
                    timeLeft--;
                    let mins = Math.floor(timeLeft / 60);
                    let secs = timeLeft % 60;
                    timerDisplay.innerText = `⏱ ${mins}:${secs < 10 ? '0' : ''}${secs}`;
                }, 1000);
            }

            let recognition;
            let isRecording = false;

            if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                recognition = new SpeechRecognition();
                recognition.lang = 'en-US';
                recognition.continuous = false;

                recognition.onresult = (event) => {
                    const text = event.results[0][0].transcript;
                    userInput.value = text;
                    sendText();
                };

                recognition.onend = () => {
                    isRecording = false;
                    micBtn.classList.remove('recording');
                };
            }

            function toggleSpeech() {
                startTimer();
                if (!recognition) {
                    alert("Speech recognition is not supported on this browser device.");
                    return;
                }
                if (isRecording) {
                    recognition.stop();
                } else {
                    recognition.start();
                    isRecording = true;
                    micBtn.classList.add('recording');
                }
            }

            function addMessage(text, isUser) {
                const div = document.createElement('div');
                div.className = `msg ${isUser ? 'user' : 'ai'}`;
                div.innerText = text;
                chat.appendChild(div);
                chat.scrollTop = chat.scrollHeight;
            }

            async function sendText() {
                startTimer();
                const text = userInput.value.trim();
                if (!text) return;

                addMessage(text, true);
                userInput.value = '';

                try {
                    const res = await fetch('/api/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ text: text, time_left: timeLeft })
                    });
                    const data = await res.json();

                    if (data.status === 'success') {
                        addMessage(data.reply, false);
                        const audio = new Audio(data.audio);
                        audio.play();
                    } else {
                        addMessage("Error: " + data.message, false);
                    }
                } catch (e) {
                    addMessage("Connection error!", false);
                }
            }

            function handleKey(e) {
                if (e.key === 'Enter') sendText();
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_code)
