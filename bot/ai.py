
import os
from groq import Groq
from gtts import gTTS

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
    }
    
    prompt = prompts.get(part, prompts["part1"])
    return get_ai_response([{"role": "user", "content": prompt}])
