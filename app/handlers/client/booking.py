from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import asyncpg
from datetime import datetime, timedelta

from app.utils.config_loader import DATABASE_URL, MASTER_ID

router = Router()

@router.message(Command("book"))
async def book_start(message: types.Message):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="💅 Маникюр", callback_data="service_Маникюр")
    keyboard.button(text="💇 Стрижка", callback_data="service_Стрижка")
    keyboard.button(text="💆 Массаж", callback_data="service_Массаж")
    keyboard.adjust(1)
    await message.answer("Выбери услугу:", reply_markup=keyboard.as_markup())

@router.callback_query(F.data.startswith("service_"))
async def choose_time(callback: types.CallbackQuery):
    service = callback
