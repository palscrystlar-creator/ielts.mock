"""
Groq API va gTTS orqali intellektual va avtomatik suhbatlashuvchi AI moduli.
"""

import os
from groq import Groq
from gtts import gTTS

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
CHAT_MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """Sen ko'p qirrali AI yordamchisan.

Sening ishlash qoidalaring:
1. Agar foydalanuvchi INGLIZ TILIDA biror gap yozsa yoki gapirsa (IELTS practice qilayotgan bo'lsa):
   - Sen zaharli, juda qattiqqo'l, sensiraydigan va kamsitadigan IELTS Coachga aylanasan.
   - Uning ingliz tilidagi xatolarini yuziga shartta sol, zaharxanda qil va o'zbek tilida sensirab, qisqa va o'tkir qilib tuzatib ber.

2. Agar foydalanuvchi O'ZBEK TILIDA yoki shunchaki salom-alik, erkin muloqot uchun yozsa:
   - Sen juda samimiy, do'stona, aqlli va xushfe'l AI hamrohsan.
   - Foydalanuvchi bilan o'zbek tilida erkin, samimiy va qiziqarli suhbat qur.
"""


def smart_reply(user_text: str) -> str:
    """Inglizcha bo'lsa Coach bo'lib urishadi, o'zbekcha bo'lsa samimiy suhbatlashadi."""
    resp = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text}
        ],
        temperature=0.7,
    )
    return resp.choices[0].message.content.strip()


def transcribe_audio(file_path: str) -> str:
    """Ovozni matnga o'girish (Whisper orqali)"""
    with open(file_path, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="whisper-large-v3-turbo",
            file=f,
            language="en"
        )
    return transcript.text


def text_to_speech(text: str, output_path: str):
    """Matnni ovozga o'girish (gTTS)"""
    tts = gTTS(text=text, lang="uz")
    tts.save(output_path)
# Groq mijozini ishga tushiramiz
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def get_ai_response(messages: list) -> str:
    """Foydalanuvchi va AI o'rtasidagi suhbatni davom ettirish."""
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Xatolik yuz berdi: {str(e)}"

def evaluate_speaking_test(user_answers: list) -> str:
    """3-qism tugagach, barcha javoblarni tahlil qilib IELTS Band Score chiqaradi."""
    formatted_answers = ""
    for idx, item in enumerate(user_answers, 1):
        q = item.get('question', 'N/A')
        a = item.get('answer', 'N/A')
        formatted_answers += f"\nSavol {idx}: {q}\nJavob {idx}: {a}\n"

    prompt = f"""
    You are an official Senior IELTS Speaking Examiner. 
    Evaluate the following candidate's answers across all parts of the IELTS Speaking Test:

    {formatted_answers}

    Provide a professional, detailed assessment in the following format:

    🎯 **OVERALL BAND SCORE: X.X**

    📊 **Detailed Criteria Scores:**
    - **Fluency and Coherence:** X.X
    - **Lexical Resource (Vocabulary):** X.X
    - **Grammatical Range & Accuracy:** X.X
    - **Pronunciation (estimated):** X.X

    💡 **Detailed Feedback:**
    - **Strengths:** (What the candidate did well)
    - **Weaknesses & Grammatical Errors:** (Specific corrections for mistakes made)
    - **Vocabulary Improvements:** (Better C1/C2 words they could have used)
    - **Tips for Band Upgrade:** (Actionable advice to reach a higher score)

    Keep the feedback clear, constructive, and directly based on their provided answers.
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Baholashda xatolik bo'ldi: {str(e)}"

def text_to_speech(text: str, output_path: str):
    """Matnni ingliz tilida talaffuz qilib, MP3 fayl sifatida saqlaydi."""
    tts = gTTS(text=text, lang='en', slow=False)
    tts.save(output_path)
def generate_question(part: str = "part1") -> str:
    """Mini App uchun IELTS savolini generatsiya qilish."""
    prompts = {
        "part1": "Generate 1 typical IELTS Speaking Part 1 question about daily life, hometown, work, or hobbies. Output ONLY the question text.",
        "part2": "Generate 1 IELTS Speaking Part 2 Cue Card topic with 3 bullet points. Output ONLY the Cue Card text.",
        "part3": "Generate 1 abstract IELTS Speaking Part 3 discussion question. Output ONLY the question text."
    """
Groq API va gTTS orqali AI funksiyalari (100% tekin):
- transcribe_audio: Groq Whisper orqali ovozni matnga aylantirish
- text_to_speech: gTTS orqali matnni ovozli mp3 ga aylantirish (Tekin!)
- correct_and_explain: Sensiraydigan va kamsitadigan zaharxanda Coach
"""

import os
import json
from groq import Groq
from gtts import gTTS

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

CHAT_MODEL = "llama-3.3-70b-versatile"
WHISPER_MODEL = "whisper-large-v3-turbo"

IELTS_PARTS = {
    "part1": "IELTS Speaking Part 1 - oddiy shaxsiy savol",
    "part2": "IELTS Speaking Part 2 - cue card topshirig'i",
    "part3": "IELTS Speaking Part 3 - tahliliy savol",
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


def text_to_speech(text: str, out_path: str) -> str:
    """gTTS orqali matnni ovozli mp3 faylga aylantiradi (100% tekin)."""
    # Inglizcha matnlar uchun 'en' yoki o'zbekcha tushuntirishlar uchun 'en' ishlatamiz (gTTS o'zbek tilini ham o'qiydi, lekin ingliz tilida tabiiyroq chiqadi)
    tts = gTTS(text=text, lang='en', slow=False)
    tts.save(out_path)
    return out_path


def generate_question(part: str) -> str:
    prompt = f"Sen tajribali IELTS examinersan. {IELTS_PARTS[part]}. Faqat BITTA original savol yoz (ingliz tilida), qo'shimcha izoh yozma."
    resp = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=1.0,
    )
    return resp.choices[0].message.content.strip()


def evaluate_answer(question: str, answer: str, part: str) -> dict:
    prompt = f"Bo'lim: {part}\nSavol: {question}\nJavob: {answer}\nJSON formatida bahola (band_estimate, strengths, errors, improved_version, tip). Izoh yozma."
    resp = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        response_format={"type": "json_object"},
    )
    return json.loads(resp.choices[0].message.content)


def final_report(history: list) -> dict:
    transcript = "\n\n".join(f"Savol: {h['question']}\nJavob: {h['answer']}" for h in history)
    prompt = f"Transkript:\n{transcript}\nYakuniy hisobotni JSON formatida ber (overall_band, fluency_coherence, lexical_resource, grammar_range_accuracy, pronunciation_note, top_advice)."
    resp = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        response_format={"type": "json_object"},
    )
    return json.loads(resp.choices[0].message.content)


def correct_and_explain(user_text: str) -> str:
    """Sensiraydigan, kamsitadigan va sarkazm bilan xatolarni ko'rsatuvchi AI Coach."""
    prompt = f"""Sen IELTS bo'yicha juda kamsituvchi, foydalanuvchining bilimini pastga uradigan va zaharxanda (sarkastik) AI Coachsan.
Sening maqsading — foydalanuvchiga FAQAT "SENSIRAB" (sen, sening, deyapsan, yozgansan) murojaat qilish. Sizlash umuman MUMKIN EMAS.
Sening vazifang so'kinmasdan, lekin foydalanuvchiga uning ingliz tili qanchalik achinarli darajada ekanini zaharli va kamsituvchi tonda aytish.

Talaba shuni yozdi yoki gapirdi (ingliz tilida): "{user_text}"

Vazifang:
1. Darhol uni va uning javobini zaharxanda va kamsitish bilan qarshilab ol (faqat sensirab!).
2. Jumlaning AYNAN qaysi qismida xato borligini ko'rsat (❌ Achinarli xato).
3. Nima uchun bu xato ekanini o'zbekcha kamsitib, sensirab tushuntir.
4. To'g'ri variantini yoz (✅ To'g'ri variant).

Javobni o'zbek tilida, so'kinishlarsiz, lekin juda achchiq, sarkastik, kamsituvchi va FAQAT SENSIRAB yoz. Qisqa va o'tkir qil (3-5 qatordan oshmasin, chunki ovozli xabar qilib yuboriladi)."""

    resp = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
    )
    return resp.choices[0].message.content.strip()
    }
    
    prompt = prompts.get(part, prompts["part1"])
    return get_ai_response([{"role": "user", "content": prompt}])
