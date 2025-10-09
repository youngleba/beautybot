from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
import asyncpg
from datetime import datetime, timedelta

from app.utils.config_loader import DATABASE_URL, MASTER_ID

router = Router()

@router.message(types.Message)
async def start_handler(message: types.Message):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="💅 Записаться", callback_data="book_start")
    await message.answer("Добро пожаловать! Нажми кнопку, чтобы записаться на услугу.", reply_markup=keyboard.as_markup())

@router.callback_query(F.data == "book_start")
async def book_start(callback: types.CallbackQuery):
    keyboard = InlineKeyboardBuilder()
    services = ["Маникюр", "Стрижка", "Массаж"]
    for service in services:
        keyboard.button(text=service, callback_data=f"service_{service}")
    keyboard.adjust(1)
    await callback.message.edit_text("Выбери услугу:", reply_markup=keyboard.as_markup())

@router.callback_query(F.data.startswith("service_"))
async def choose_time(callback: types.CallbackQuery):
    service = callback.data.split("_", 1)[1]
    # Здесь простой пример свободного времени — позже можно заменить реальной логикой
    keyboard = InlineKeyboardBuilder()
    for time in ["10:00", "12:30", "15:00"]:
        keyboard.button(text=time, callback_data=f"time_{service}_{time}")
    keyboard.adjust(2)
    await callback.message.edit_text(f"Выбрана услуга: {service}\nТеперь выбери время:", reply_markup=keyboard.as_markup())

@router.callback_query(F.data.startswith("time_"))
async def confirm_booking(callback: types.CallbackQuery):
    _, service, time = callback.data.split("_", 2)
    client_id = callback.from_user.id
    username = callback.from_user.username
    full_name = callback.from_user.full_name

    conn = await asyncpg.connect(DATABASE_URL)

    await conn.execute("""
        INSERT INTO clients (id, username, full_name)
        VALUES ($1, $2, $3)
        ON CONFLICT (id) DO NOTHING
    """, client_id, username, full_name)

    service_id_row = await conn.fetchrow(
        "SELECT id FROM services WHERE name=$1", service
    )
    if not service_id_row:
        await conn.execute(
            "INSERT INTO services (name, duration_minutes) VALUES ($1, $2)", service, 120
        )
        service_id_row = await conn.fetchrow(
            "SELECT id FROM services WHERE name=$1", service
        )
    service_id = service_id_row['id']

    start_time_str = f"2025-10-09 {time}:00"
    start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
    end_time = start_time + timedelta(hours=2)

    await conn.execute(
        """
        INSERT INTO appointments (client_id, service_id, start_time, end_time, status)
        VALUES ($1, $2, $3, $4, 'pending')
        """,
        client_id, service_id, start_time, end_time
    )
    await conn.close()

    await callback.message.edit_text(f"✅ Заявка отправлена мастеру!\nУслуга: {service}\nВремя: {time}")

    # Уведомление мастеру
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="✅ Подтвердить", callback_data=f"approve_{client_id}_{service_id}_{time}")
    keyboard.button(text="❌ Отклонить", callback_data=f"reject_{client_id}_{service_id}_{time}")
    keyboard.adjust(2)

    await callback.bot.send_message(
        MASTER_ID,
        f"💬 Новая запись:\nКлиент: {full_name}\nУслуга: {service}\nВремя: {time}",
        reply_markup=keyboard.as_markup()
    )
