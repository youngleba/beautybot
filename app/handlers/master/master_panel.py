from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import asyncpg
from datetime import datetime

from app.utils.config_loader import DATABASE_URL, MASTER_ID

router = Router()

@router.message(Command("master"))
async def master_start(message: types.Message):
    if message.from_user.id != MASTER_ID:
        await message.answer("❌ У вас нет доступа к этой панели")
        return

    await show_appointments(message)

async def show_appointments(message: types.Message):
    conn = await asyncpg.connect(DATABASE_URL)

    rows = await conn.fetch("SELECT * FROM appointments ORDER BY start_time")

    if not rows:
        await message.answer("Записей пока нет.")
        await conn.close()
        return

    text = "📅 Текущие записи:\n\n"
    for row in rows:
        status_icons = {
            "pending": "⏳",
            "approved": "✅",
            "rejected": "❌",
            "canceled": "🚫"
        }
        icon = status_icons.get(row['status'], "")
        start_str = row['start_time'].strftime("%d.%m.%Y %H:%M")
        end_str = row['end_time'].strftime("%H:%M")
        text += f"{icon} Клиент ID: {row['client_id']}, Услуга ID: {row['service_id']}\n" \
                f"Время: {start_str} - {end_str}, Статус: {row['status']}\n\n"

    keyboard = InlineKeyboardBuilder()
    await message.answer(text, reply_markup=keyboard.as_markup())
