# ~/beautybot/app/keyboards/main_kb.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_kb() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="📅 Записаться")],
        [KeyboardButton(text="💰 Мои бонусы"), KeyboardButton(text="📖 Мои записи")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

