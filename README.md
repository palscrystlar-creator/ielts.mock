# IELTS Speaking Telegram Bot 🗣

AI yordamida ishlaydigan IELTS Speaking mock test va practice boti.

## Funksiyalar

**1. IELTS Mock Test** (Telegram Mini App — alohida oynada)
- 5 ta savol: 2× Part 1, 1× Part 2 (cue card), 2× Part 3
- Har safar AI **random** savol yaratadi (takrorlanmaydi)
- Ovozli javob beriladi → Whisper matnga aylantiradi → GPT baholaydi
- Har javobdan keyin darhol feedback: band, xatolar, yaxshilangan variant
- Oxirida umumiy hisobot (band + maslahatlar)

**2. AI Assistant** (oddiy chatda)
- Ovozli yoki matnli xabar yuboriladi
- AI aynan qaysi joyda xato borligini tushuntiradi va to'g'rilaydi (ielts.gg uslubida)

## Texnologiyalar

- **Backend:** FastAPI + aiogram 3 (Telegram webhook orqali)
- **AI:** OpenAI — Whisper (STT), GPT-4o-mini (savol/baholash), TTS (ovoz)
- **Frontend:** Telegram Mini App (oddiy HTML/CSS/JS, Telegram WebApp SDK)
- **Hosting:** Render.com (bepul tarif)

---

## 1-qadam — Telegram bot yaratish

1. Telegram'da [@BotFather](https://t.me/BotFather) ga yozing
2. `/newbot` yuboring, nom va username bering
3. Sizga **token** beradi (masalan `123456:AAExample...`) — buni saqlab qo'ying

## 2-qadam — OpenAI API key

[platform.openai.com/api-keys](https://platform.openai.com/api-keys) sahifasidan key oling (sizda allaqachon bor).

> ⚠️ Whisper, GPT-4o-mini va TTS pullik xizmatlar. Xarajatni nazorat qilish uchun OpenAI dashboard'da **usage limit** qo'ying.

## 3-qadam — GitHub'ga yuklash

```bash
cd ielts-bot
git add .
git commit -m "IELTS speaking bot"
```

GitHub'da yangi **private yoki public repo** yarating, so'ng:

```bash
git remote add origin https://github.com/USERNAME/REPO_NOMI.git
git branch -M main
git push -u origin main
```

## 4-qadam — Render.com'da deploy qilish

1. [render.com](https://render.com) ga GitHub akkaunt bilan kiring
2. **New +** → **Web Service** → repo'ni tanlang
3. Sozlamalar (agar `render.yaml` avtomatik o'qilmasa, qo'lda kiriting):
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free
4. **Environment Variables** bo'limida qo'shing:
   - `TELEGRAM_BOT_TOKEN` = BotFather'dan olingan token
   - `OPENAI_API_KEY` = OpenAI key
   - `MINIAPP_URL` = hozircha bo'sh qoldiring
5. **Create Web Service** bosing va deploy tugashini kuting

## 5-qadam — Mini App URL'ni ulash

Deploy tugagach, Render sizga manzil beradi, masalan:
`https://ielts-speaking-bot.onrender.com`

1. Render'dagi **Environment** bo'limiga qayting
2. `MINIAPP_URL` qiymatini shunga o'zgartiring:
   `https://ielts-speaking-bot.onrender.com/miniapp/`
3. Saqlang — Render avtomatik qayta deploy qiladi (1-2 daqiqa)

Webhook esa `RENDER_EXTERNAL_URL` orqali **avtomatik** o'rnatiladi (kodda shu ishlangan), qo'shimcha ish qilish shart emas.

## 6-qadam — Botni sinash

Telegram'da botingizga o'ting → `/start` → tugmalarni bosing:
- 🗣 **IELTS Mock Test** — Mini App ochiladi, mikrofonga ruxsat bering
- 💬 **AI Assistant** — chatda ovozli/matnli practice qiling

---

## Muhim eslatmalar

- **Bepul Render tarifi** 15 daqiqa faolliksiz qolsa "uxlab qoladi" — birinchi so'rov 30-50 soniya sekinroq javob beradi. Shaxsiy/test foydalanish uchun muammo emas.
- **Sessiya xotirasi** hozircha oddiy Python dict'da saqlanadi (RAM'da) — server qayta ishga tushsa, faol mock testlar yo'qoladi. Ko'p foydalanuvchili productionga o'tsangiz, buni Redis yoki DB'ga ko'chirish tavsiya etiladi.
- **Xarajat:** har bir mock savol ≈ Whisper (audio uzunligiga qarab) + GPT-4o-mini so'rovi + TTS. Shaxsiy test uchun juda arzon (bir necha sentga yaqin/session), lekin ko'p foydalanuvchi bo'lsa OpenAI billing'ni kuzatib turing.

## Lokal test qilish (ixtiyoriy)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # keyin .env faylni to'ldiring
uvicorn app:app --reload --port 8000
```

Webhook uchun lokalda [ngrok](https://ngrok.com) kabi tunnel kerak bo'ladi, chunki Telegram webhook'ga HTTPS manzil talab qiladi.

## Loyiha tuzilishi

```
ielts-bot/
├── app.py              # FastAPI server: webhook + Mini App API
├── bot/
│   ├── handlers.py      # /start, ovozli/matnli xabarlar
│   ├── keyboards.py     # inline tugmalar
│   └── ai.py            # OpenAI: STT, TTS, savol yaratish, baholash
├── miniapp/
│   ├── index.html        # Mock test interfeysi
│   ├── style.css
│   └── app.js            # Mikrofon yozish + API chaqiruvlari
├── requirements.txt
├── render.yaml
└── .env.example
```
