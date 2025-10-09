from aiogram import Router, types, F
from aiogram.filters import Command, CallbackQueryData
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
    await conn.close()

    if not rows:
        await message.answer("Записей пока нет.")
        return

    text = "📅 Текущие записи:\n\n"
    keyboard = InlineKeyboardBuilder()

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
        text += (
            f"{icon} Клиент ID: {row['client_id']}, Услуга ID: {row['service_id']}\n"
            f"Время: {start_str} - {end_str}, Статус: {row['status']}\n\n"
        )
        if row['status'] == 'pending':
            keyboard.button(
                text=f"✅ Подтвердить запись {row['id']}",
                callback_data=f"approve_{row['id']}"
            )
            keyboard.button(
                text=f"❌ Отклонить запись {row['id']}",
                callback_data=f"reject_{row['id']}"
            )

    if keyboard.buttons:
        keyboard.adjust(2)

    await message.answer(text, reply_markup=keyboard.as_markup())

@router.callback_query(F.data.startswith("approve_"))
async def approve_appointment(callback: types.CallbackQuery):
    if callback.from_user.id != MASTER_ID:
        await callback.answer("❌ У вас нет доступа", show_alert=True)
        return

    appointment_id = int(callback.data.split("_", 1)[1])
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute(
        "UPDATE appointments SET status = 'approved' WHERE id = $1", appointment_id
    )
    await conn.close()

    await callback.answer("✅ Запись подтверждена")
    await master_start(await callback.message.answer(""))
    
@router.callback_query(F.data.startswith("reject_"))
async def reject_appointment(callback: types.CallbackQuery):
    if callback.from_user.id != MASTER_ID:
        await callback.answer("❌ У вас нет доступа", show_alert=True)
        return

    appointment_id = int(callback.data.split("_", 1)[1])
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute(
        "UPDATE appointments SET status = 'rejected' WHERE id = $1", appointment_id
    )
    await conn.close()

    await callback.answer("❌ Запись отклонена")
    await master_start(await callback.message.answer(""))
