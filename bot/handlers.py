from aiogram import Router, F, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import os

from bot.ai import get_ai_response, evaluate_speaking_test
from bot.keyboards import get_main_keyboard

router = Router()

class TestState(StatesGroup):
    in_test = State()

# Test savollari strukturasi
MOCK_QUESTIONS = [
    # Part 1
    {"part": 1, "q": "Let's talk about your hometown. Where are you from?"},
    {"part": 1, "q": "What do you like most about your hometown?"},
    # Part 2
    {"part": 2, "q": "Describe a book you recently read. You should say: what it was, why you read it, and explain if you liked it."},
    # Part 3
    {"part": 3, "q": "Do you think young people read enough books nowadays?"},
    {"part": 3, "q": "How has modern technology changed reading habits?"}
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
    
    # Test ma'lumotlarini xotirada saqlaymiz
    await state.update_data(current_index=0, history=[])
    
    first_q = MOCK_QUESTIONS[0]["q"]
    part = MOCK_QUESTIONS[0]["part"]
    
    await message.answer(
        f"📍 **Part {part}**\n\n1-Savol:\n{first_q}\n\n*(Javobingizni matn yoki ovoz shaklida yuboring)*",
        parse_mode="Markdown"
    )

@router.message(TestState.in_test)
async def process_test_answer(message: types.Message, state: FSMContext):
    data = await state.get_data()
    current_index = data.get("current_index", 0)
    history = data.get("history", [])
    
    # Foydalanuvchi javobi
    user_answer = message.text or "Ovozli javob berildi"
    current_q = MOCK_QUESTIONS[current_index]["q"]
    
    # Javobni tarixga saqlash
    history.append({"question": current_q, "answer": user_answer})
    
    next_index = current_index + 1
    
    # Agar savollar tugasa -> 3 ta Part tamomlandi!
    if next_index >= len(MOCK_QUESTIONS):
        await message.answer("⏳ **Rahmat! 3-qism ham yakunlandi. AI javoblaringizni tahlil qilmoqda...**", parse_mode="Markdown")
        
        # Groq orqali Band Score va tahlil olish
        result = evaluate_speaking_test(history)
        
        await message.answer(
            f"🎉 **IELTS Mock Test Natijangiz:**\n\n{result}",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        await state.clear()
    else:
        # Keyingi savolga o'tish
        await state.update_data(current_index=next_index, history=history)
        next_q = MOCK_QUESTIONS[next_index]["q"]
        next_part = MOCK_QUESTIONS[next_index]["part"]
        
        await message.answer(
            f"📍 **Part {next_part}**\n\n{next_index + 1}-Savol:\n{next_q}",
            parse_mode="Markdown"
        )
