from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.database import db
from app.utils.config_loader import MASTER_ID
import asyncpg

router = Router()

# === 1. Команда /book ===
@router.message(Command("book"))
async def book_start(message: types.Message):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="💅 Маникюр", callback_data="service_Маникюр")
    keyboard.button(text="💇 Стрижка", callback_data="service_Стрижка")
    keyboard.button(text="💆 Массаж", callback_data="service_Массаж")
    keyboard.adjust(1)
    await message.answer("Выбери услугу:", reply_markup=keyboard.as_markup())

# === 2. Выбор времени ===
@router.callback_query(F.data.startswith("service_"))
async def choose_time(callback: types.CallbackQuery):
    service = callback.data.split("_", 1)[1]
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="10:00", callback_data=f"time_{service}_10:00")
    keyboard.button(text="12:00", callback_data=f"time_{service}_12:00")
    keyboard.button(text="15:00", callback_data=f"time_{service}_15:00")
    keyboard.adjust(2)
    await callback.message.edit_text(f"Выбрана услуга: {service}\nТеперь выбери время:", reply_markup=keyboard.as_markup())

# === 3. Отправка мастеру на подтверждение ===
@router.callback_query(F.data.startswith("time_"))
async def confirm_booking(callback: types.CallbackQuery):
    parts = callback.data.split("_", 2)
    service, time = parts[1], parts[2]
    client_id = callback.from_user.id

    conn = await asyncpg.connect(db.DATABASE_URL)
    await conn.execute("""
        INSERT INTO appointments (client_id, service, datetime, status)
        VALUES ($1, $2, $3, 'pending')
    """, client_id, service, f"2025-10-09 {time}:00")
    await conn.close()

    await callback.message.edit_text(f"✅ Заявка отправлена мастеру на подтверждение!\nУслуга: {service}\nВремя: {time}")

    # уведомление мастеру
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="✅ Подтвердить", callback_data=f"approve_{client_id}_{service}_{time}")
    keyboard.button(text="❌ Отклонить", callback_data=f"reject_{client_id}_{service}_{time}")
    keyboard.adjust(2)

    await callback.bot.send_message(
        MASTER_ID,
        f"💬 Новая запись:\nКлиент: {callback.from_user.full_name}\nУслуга: {service}\nВремя: {time}",
        reply_markup=keyboard.as_markup()
    )

# === 4. Подтверждение мастером ===
@router.callback_query(F.data.startswith("approve_"))
async def approve(callback: types.CallbackQuery):
    _, client_id, service, time = callback.data.split("_", 3)
    client_id = int(client_id)
    conn = await asyncpg.connect(db.DATABASE_URL)
    await conn.execute("""
        UPDATE appointments SET status='approved'
        WHERE client_id=$1 AND service=$2 AND datetime=$3
    """, client_id, service, f"2025-10-09 {time}:00")
    await conn.close()

    await callback.bot.send_message(client_id, f"✅ Ваша запись подтверждена!\n💅 Услуга: {service}\n🕐 Время: {time}")
    await callback.message.edit_text(f"✅ Запись подтверждена: {service}, {time}")

# === 5. Отклонение мастером ===
@router.callback_query(F.data.startswith("reject_"))
async def reject(callback: types.CallbackQuery):
    _, client_id, service, time = callback.data.split("_", 3)
    client_id = int(client_id)
    conn = await asyncpg.connect(db.DATABASE_URL)
    await conn.execute("""
        UPDATE appointments SET status='rejected'
        WHERE client_id=$1 AND service=$2 AND datetime=$3
    """, client_id, service, f"2025-10-09 {time}:00")
    await conn.close()

    await callback.bot.send_message(client_id, f"❌ Ваша запись отклонена.\n💅 Услуга: {service}\n🕐 Время: {time}")
    await callback.message.edit_text(f"🚫 Запись отклонена: {service}, {time}")
