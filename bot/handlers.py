from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import FSInputFile
import os

from bot.ai import get_ai_response, evaluate_speaking_test, text_to_speech
from bot.keyboards import get_main_keyboard

router = Router()

class TestState(StatesGroup):
    in_test = State()

# Test bosqichlari strukturasi
TEST_STRUCTURE = [
    {"part": 1, "prompt": "Generate a typical IELTS Speaking Part 1 topic and 1 simple question about hometown, work, studies, or hobbies. Output ONLY the question text."},
    {"part": 1, "prompt": "Generate another IELTS Speaking Part 1 question related to daily life. Output ONLY the question text."},
    {"part": 2, "prompt": "Generate an IELTS Speaking Part 2 Cue Card (Describe a topic with 3-4 bullet points). Keep it concise. Output ONLY the Cue Card text."},
    {"part": 3, "prompt": "Generate a complex IELTS Speaking Part 3 abstract question related to the Part 2 topic. Output ONLY the question text."},
    {"part": 3, "prompt": "Generate another IELTS Speaking Part 3 discussion question. Output ONLY the question text."}
]

@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    text = (
        "👋 **Xush kelibsiz! Men sizning IELTS Speaking AI Yordamchingizman.**\n\n"
        "Mock test topshirish uchun tugmani bosing yoki Mini App'dan foydalaning!"
    )
    await message.answer(text, reply_markup=get_main_keyboard(), parse_mode="Markdown")

@router.message(F.text == "🎯 Start Mock Test")
async def start_mock_test(message: types.Message, state: FSMContext):
    await state.set_state(TestState.in_test)
    await state.update_data(current_index=0, history=[])
    
    # 1-savolni AI yordamida generatsiya qilamiz
    await send_question(message, state, 0)

async def send_question(message: types.Message, state: FSMContext, index: int):
    part_info = TEST_STRUCTURE[index]
    part_num = part_info["part"]
    
    # AI orqali har safar yangi savol yaratamiz
    q_prompt = part_info["prompt"]
    question_text = get_ai_response([{"role": "user", "content": q_prompt}])
    
    # Savolni saqlaymiz
    data = await state.get_data()
    data["current_question"] = question_text
    await state.set_data(data)
    
    # Ovozli fayl yaratamiz (gTTS)
    audio_filename = f"question_{message.from_user.id}.mp3"
    try:
        text_to_speech(question_text, audio_filename)
        voice_file = FSInputFile(audio_filename)
        
        # Ovozli xabar va matnni yuboramiz
        await message.answer(f"📍 **Part {part_num}** ({index + 1}/5-savol):")
        await message.answer_voice(voice=voice_file, caption=question_text)
        
        # Faylni o'chiramiz
        if os.path.exists(audio_filename):
            os.remove(audio_filename)
    except Exception as e:
        # Agar ovozda xatolik bo'lsa, shunchaki matn yuboradi
        await message.answer(f"📍 **Part {part_num}** ({index + 1}/5-savol):\n\n{question_text}")

@router.message(TestState.in_test)
async def process_test_answer(message: types.Message, state: FSMContext):
    data = await state.get_data()
    current_index = data.get("current_index", 0)
    history = data.get("history", [])
    current_question = data.get("current_question", "")
    
    user_answer = message.text or "Ovozli javob berildi"
    history.append({"question": current_question, "answer": user_answer})
    
    next_index = current_index + 1
    
    if next_index >= len(TEST_STRUCTURE):
        await message.answer("⏳ **Rahmat! Test yakunlandi. AI javoblaringizni tahlil qilib, IELTS Band Score hisoblamoqda...**", parse_mode="Markdown")
        
        # IELTS Band Score tahlili
        result = evaluate_speaking_test(history)
        
        await message.answer(
            f"🎉 **IELTS Mock Test Natijangiz:**\n\n{result}",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        await state.clear()
    else:
        await state.update_data(current_index=next_index, history=history)
        await send_question(message, state, next_index)
