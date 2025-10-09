from aiogram import Router, types
import asyncpg
from datetime import datetime
from app.utils.config_loader import DATABASE_URL
from aiogram.filters import Command

router = Router()

@router.message(Command("profile"))
async def profile_info(message: types.Message):
    client_id = message.from_user.id
    conn = await asyncpg.connect(DATABASE_URL)
    rows = await conn.fetch(
        """
        SELECT a.id, s.name, a.start_time, a.end_time, a.status
        FROM appointments a
        JOIN services s ON a.service_id = s.id
        WHERE a.client_id = $1
        ORDER BY a.start_time DESC
        """,
        client_id
    )
    await conn.close()

    if not rows:
        await message.answer("📃 У вас пока нет записей.")
        return

    text = "📋 Ваша история записей:\n\n"
    for row in rows:
        icon = {
            "pending": "⏳",
            "approved": "✅",
            "rejected": "❌",
            "canceled": "🚫"
        }.get(row['status'], "")
        start_str = row['start_time'].strftime("%d.%m.%Y %H:%M")
        end_str = row['end_time'].strftime("%H:%M")
        text += (
            f"{icon} Запись ID: {row['id']}\n"
            f"Услуга: {row['name']}\n"
            f"Время: {start_str} - {end_str}\n"
            f"Статус: {row['status']}\n\n"
        )
    await message.answer(text)
