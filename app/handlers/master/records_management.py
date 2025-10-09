from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import asyncpg
from datetime import datetime, timedelta
from app.utils.config_loader import DATABASE_URL, MASTER_ID

router = Router()

@router.message(Command("records"))
async def records_panel(message: types.Message):
    if message.from_user.id != MASTER_ID:
        await message.answer("❌ Нет доступа")
        return
    await show_pending_records(message)

async def show_pending_records(message: types.Message):
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        rows = await conn.fetch(
            "SELECT * FROM appointments WHERE status='pending' ORDER BY start_time"
        )
        await conn.close()
    except Exception as e:
        await message.answer("Ошибка доступа к базе данных. Попробуйте позже.")
        return

    if not rows:
        await message.answer("Пока нет новых заявок.")
        return

    text = "📋 Заявки на обработку:\n\n"
    keyboard = InlineKeyboardBuilder()
    for row in rows:
        start_str = row['start_time'].strftime("%d.%m.%Y %H:%M")
        end_str = row['end_time'].strftime("%H:%M")
        text += f"ID: {row['id']} Клиент: {row['client_id']}\nВремя: {start_str} - {end_str}\n\n"
        keyboard.button(text=f"✅ Подтвердить {row['id']}", callback_data=f"approve_{row['id']}")
        keyboard.button(text=f"❌ Отменить {row['id']}", callback_data=f"cancel_{row['id']}")
    keyboard.adjust(2)
    await message.answer(text, reply_markup=keyboard.as_markup())

@router.callback_query(F.data.startswith("approve_"))
async def approve_record(callback: types.CallbackQuery):
    if callback.from_user.id != MASTER_ID:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    try:
        app_id = int(callback.data.split("_")[1])
        conn = await asyncpg.connect(DATABASE_URL)
        await conn.execute("UPDATE appointments SET status='approved' WHERE id=$1", app_id)
        await conn.close()
        await callback.answer("✅ Подтверждено")
    except Exception as e:
        await callback.answer("Ошибка при подтверждении записи", show_alert=True)
        return
    await records_panel(await callback.message.answer(""))

@router.callback_query(F.data.startswith("cancel_"))
async def cancel_record(callback: types.CallbackQuery):
    if callback.from_user.id != MASTER_ID:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    try:
        app_id = int(callback.data.split("_")[1])
        conn = await asyncpg.connect(DATABASE_URL)
        await conn.execute("UPDATE appointments SET status='canceled' WHERE id=$1", app_id)
        await conn.close()
        await callback.answer("🚫 Отменено")
    except Exception as e:
        await callback.answer("Ошибка при отмене записи", show_alert=True)
        return
    await records_panel(await callback.message.answer(""))
