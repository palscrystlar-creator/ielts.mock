import os
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

def get_main_keyboard() -> ReplyKeyboardMarkup:
    miniapp_url = os.getenv("MINIAPP_URL", "https://ielts-mock-6yvx.onrender.com/miniapp/")
    
    kb = [
        [
            KeyboardButton(text="🎯 Start Mock Test"),
            KeyboardButton(text="📱 Mini App", web_app=WebAppInfo(url=miniapp_url))
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
