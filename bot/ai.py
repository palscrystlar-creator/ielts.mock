"""
Groq API orqali AI funksiyalari (100% tekin):
- transcribe_audio: Groq Whisper-large-v3-turbo orqali ovozni matnga aylantirish
- generate_question, evaluate_answer, final_report, correct_and_explain: Groq Llama 3.3
"""

import os
import json
from groq import Groq
from gtts import gTTS

def text_to_speech(text: str, output_path: str):
    """Matnni ingliz tilida talaffuz qilib, MP3 fayl sifatida saqlaydi."""
    tts = gTTS(text=text, lang='en', slow=False)
    tts.save(output_path)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

CHAT_MODEL = "llama-3.3-70b-versatile"
WHISPER_MODEL = "whisper-large-v3-turbo"

IELTS_PARTS = {
    "part1": "IELTS Speaking Part 1 - oddiy shaxsiy savol (uy, ish/o'qish, hobbi, oila, sevimli narsalar kabi kundalik mavzularda, bitta qisqa savol)",
    "part2": "IELTS Speaking Part 2 - cue card topshirig'i. Formatda yoz: 'Describe a/an ... You should say: - ... - ... - ... and explain ...'",
    "part3": "IELTS Speaking Part 3 - chuqurroq, tahliliy va fikr-mulohaza talab qiladigan savol (jamiyat, texnologiya, ta'lim, madaniyat kabi mavzularda)",
}


def transcribe_audio(file_path: str) -> str:
    """Audio faylni Groq Whisper orqali ingliz tilidagi matnga aylantiradi."""
    with open(file_path, "rb") as f:
        result = client.audio.transcriptions.create(
            model=WHISPER_MODEL,
            file=f,
            language="en",
        )
    return result.text.strip()


def generate_question(part: str) -> str:
    """Berilgan IELTS Speaking bo'limi uchun random savol/topic yaratadi."""
    prompt = f"""Sen tajribali IELTS examinersan.
{IELTS_PARTS[part]}.

Faqat BITTA original va tasodifiy savol/topshiriq yoz (ingliz tilida).
Oldin ishlatilgan odatiy mavzularni takrorlama, yangi va xilma-xil mavzu tanla.
Javobingda FAQAT savol matni bo'lsin, hech qanday izoh yoki qo'shimcha yozma."""

    resp = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=1.0,
    )
    return resp.choices[0].message.content.strip()


def evaluate_answer(question: str, answer: str, part: str) -> dict:
    """Bitta savol-javob juftligini baholaydi va o'zbek tilida feedback qaytaradi."""
    prompt = f"""Sen tajribali IELTS Speaking examinersan. Quyidagi javobni bahola.

Bo'lim: {part}
Savol: {question}
Talabaning og'zaki javobi (matnga aylantirilgan): "{answer}"

Faqat quyidagi JSON formatida javob ber (boshqa hech narsa yozma, izoh qo'shma, ```json taglarini ham ishlatma):
{{
  "band_estimate": "taxminiy band, masalan '6.0-6.5'",
  "strengths": "javobning kuchli tomonlari, o'zbek tilida, 1-2 gap",
  "errors": "aniq grammatik/lug'aviy xatolar va ular qaysi so'z yoki jumlada ekani, o'zbek tilida tushuntirilgan",
  "improved_version": "javobning yaxshilangan, tabiiyroq ingliz tilidagi varianti",
  "tip": "keyingi safar uchun bitta aniq maslahat, o'zbek tilida"
}}"""

    resp = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        response_format={"type": "json_object"},
    )
    return json.loads(resp.choices[0].message.content)


def final_report(history: list) -> dict:
    """Butun mock test tarixi asosida yakuniy umumiy hisobot yaratadi."""
    transcript = "\n\n".join(
        f"Savol: {h['question']}\nJavob: {h['answer']}" for h in history
    )
    prompt = f"""Quyida to'liq IELTS Speaking mock test transkripti berilgan:

{transcript}

Shu asosida yakuniy umumiy hisobot yoz. Faqat quyidagi JSON formatida (boshqa hech narsa yozma, ```json taglarini ham ishlatma):
{{
  "overall_band": "taxminiy umumiy band, masalan '6.5'",
  "fluency_coherence": "qisqa baho, o'zbek tilida",
  "lexical_resource": "qisqa baho, o'zbek tilida",
  "grammar_range_accuracy": "qisqa baho, o'zbek tilida",
  "pronunciation_note": "eslatma: talaffuz faqat matn orqali taxminiy baholanmoqda, o'zbek tilida",
  "top_advice": ["eng muhim maslahat 1", "maslahat 2", "maslahat 3"]
}}"""

    resp = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        response_format={"type": "json_object"},
    )
    return json.loads(resp.choices[0].message.content)


def correct_and_explain(user_text: str) -> str:
    """Erkin practice rejimi uchun xatolar va tushuntirish qaytaradi."""
    prompt = f"""Sen ielts.gg saytidagi kabi ishlaydigan IELTS AI Speaking/Writing yordamchisan.

Talaba shuni yozdi yoki gapirdi (ingliz tilida): "{user_text}"

Vazifang:
1. Agar xato bo'lsa - jumlaning AYNAN qaysi qismida xato borligini ko'rsat.
2. Nima uchun bu xato ekanini o'zbek tilida, qisqa va tushunarli tushuntir.
3. To'g'ri variantini yoz.
4. Agar xato bo'lmasa - tabrikla va gapni yanada tabiiyroq/yuqori bandga mos qiladigan boyroq so'z yoki tuzilma taklif qil.

Javobni o'zbek tilida, do'stona, lekin aniq va tuzilgan formatda yoz (masalan ❌ Xato / ✅ To'g'ri belgilari bilan). Juda uzun yozma, 5-8 qatordan oshmasin."""

    resp = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
    )
    return resp.choices[0].message.content.strip()
