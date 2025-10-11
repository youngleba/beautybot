from aiogram import Dispatcher, types
from aiogram.dispatcher.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def register_start_handler(dp: Dispatcher):
    dp.register_message_handler(start_command, commands=['start'])

async def start_command(message: types.Message):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("💅 Записаться", callback_data="book_start"))
    await message.reply(
        "👋 Привет! Это BeautyBot. Запишись на услугу или напиши /panel, если ты мастер.",
        reply_markup=keyboard
    )
