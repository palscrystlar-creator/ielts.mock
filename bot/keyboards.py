from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard() -> ReplyKeyboardMarkup:
    kb = [
        [
            KeyboardButton(text="🎯 Start Mock Test")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
