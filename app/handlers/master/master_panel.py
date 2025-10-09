import logging
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import asyncpg
from app.utils.config_loader import DATABASE_URL, MASTER_ID

router = Router()

@router.message(Command("master"))
async def panel(message: types.Message):
    if message.from_user.id != MASTER_ID:
        await message.answer("❌ Нет доступа.")
        return
    await show_appointments(message)

async def show_appointments(message: types.Message):
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        rows = await conn.fetch("SELECT * FROM appointments ORDER BY start_time")
        await conn.close()
    except Exception as e:
        logging.error(f"Ошибка при получении записей: {e}")
        await message.answer("Ошибка доступа к базе данных. Попробуйте позже.")
        return

    if not rows:
        await message.answer("Записей нет.")
        return

    text = "📅 Записи:\n\n"
    keyboard = InlineKeyboardBuilder()
    for row in rows:
        icons = {"pending": "⏳", "approved": "✅", "rejected": "❌", "canceled": "🚫"}
        icon = icons.get(row['status'], "")
        start_str = row['start_time'].strftime("%d.%m.%Y %H:%M")
        end_str = row['end_time'].strftime("%H:%M")
        text += (
            f"{icon} ID: {row['id']} Клиент: {row['client_id']} Услуга: {row['service_id']}\n"
            f"Время: {start_str} - {end_str}\n"
            f"Статус: {row['status']}\n\n"
        )
        if row['status'] == 'pending':
            keyboard.button(text=f"✅ Подтвердить {row['id']}", callback_data=f"approve_{row['id']}")
            keyboard.button(text=f"❌ Отклонить {row['id']}", callback_data=f"reject_{row['id']}")
    if keyboard.buttons:
        keyboard.adjust(2)
    await message.answer(text, reply_markup=keyboard.as_markup())

@router.callback_query(F.data.startswith("approve_"))
async def approve(callback: types.CallbackQuery):
    if callback.from_user.id != MASTER_ID:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    try:
        app_id = int(callback.data.split("_")[1])
        conn = await asyncpg.connect(DATABASE_URL)
        await conn.execute("UPDATE appointments SET status='approved' WHERE id=$1", app_id)
        await conn.close()
    except Exception as e:
        logging.error(f"Ошибка в approve: {e}")
        await callback.answer("Ошибка при подтверждении записи", show_alert=True)
        return
    await callback.answer("✅ Подтверждено")
    await panel(callback.message)

@router.callback_query(F.data.startswith("reject_"))
async def reject(callback: types.CallbackQuery):
    if callback.from_user.id != MASTER_ID:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    try:
        app_id = int(callback.data.split("_")[1])
        conn = await asyncpg.connect(DATABASE_URL)
        await conn.execute("UPDATE appointments SET status='rejected' WHERE id=$1", app_id)
        await conn.close()
    except Exception as e:
        logging.error(f"Ошибка в reject: {e}")
        await callback.answer("Ошибка при отклонении записи", show_alert=True)
        return
    await callback.answer("❌ Отклонено")
    await panel(callback.message)
