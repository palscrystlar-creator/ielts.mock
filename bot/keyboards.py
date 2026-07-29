import os
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

MINIAPP_URL = os.getenv("MINIAPP_URL", "https://example.onrender.com/miniapp/")


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗣 IELTS Mock Test (ovozli)", web_app=WebAppInfo(url=MINIAPP_URL))],
            [InlineKeyboardButton(text="💬 AI Assistant bilan practice", callback_data="mode_assistant")],
            [InlineKeyboardButton(text="ℹ️ Yordam", callback_data="help")],
        ]
    )


def assistant_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Bosh menyu", callback_data="mode_menu")],
        ]
    )
