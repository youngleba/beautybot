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
async def choose_date(callback: types.CallbackQuery):
    service = callback.data.split("_", 1)[1]
    keyboard = InlineKeyboardBuilder()
    # Добавляем выбор даты (сегодня, завтра, послезавтра)
    today = datetime.now().date()
    dates = {
        "today": today,
        "tomorrow": today + timedelta(days=1),
        "day_after": today + timedelta(days=2)
    }
    for label, date in dates.items():
        keyboard.button(text=date.strftime("%d.%m.%Y"), callback_data=f"date_{service}_{label}")
    keyboard.adjust(1)
    await callback.message.edit_text(f"Выбрана услуга: {service}\nТеперь выбери дату:", reply_markup=keyboard.as_markup())

@router.callback_query(F.data.startswith("date_"))
async def choose_time(callback: types.CallbackQuery):
    _, service, date_label = callback.data.split("_", 2)
    today = datetime.now().date()
    dates = {
        "today": today,
        "tomorrow": today + timedelta(days=1),
        "day_after": today + timedelta(days=2)
    }
    selected_date = dates.get(date_label)

    if not selected_date:
        await callback.message.edit_text("Ошибка выбора даты.")
        return

    # Получаем занятые слоты для даты
    conn = await asyncpg.connect(DATABASE_URL)
    rows = await conn.fetch(
        "SELECT start_time, end_time FROM appointments WHERE DATE(start_time) = $1 AND status IN ('pending', 'approved')",
        selected_date
    )
    await conn.close()

    # Извлекаем занятые времена (часы и минуты)
    busy_times = set()
    for row in rows:
        start_hour = row['start_time'].hour
        end_hour = row['end_time'].hour
        for hour in range(start_hour, end_hour):
            busy_times.add(hour)

    # Свободные времена: от 8:00 до 18:00
    all_times = {8, 9, 10, 11, 12, 13, 14, 15, 16, 17}
    free_times = all_times - busy_times

    if not free_times:
        await callback.message.edit_text("На эту дату все время занято. Выберите другую дату или сервис.")
        return

    keyboard = InlineKeyboardBuilder()
    for hour in sorted(free_times):
        time_str = f"{hour:02d}:00"
        keyboard.button(text=time_str, callback_data=f"time_{service}_{date_label}_{hour}")
    keyboard.adjust(2)
    await callback.message.edit_text(
        f"Выбрана услуга: {service}\nДата: {selected_date.strftime('%d.%m.%Y')}\nСвободное время:",
        reply_markup=keyboard.as_markup()
    )

@router.callback_query(F.data.startswith("time_"))
async def confirm_booking(callback: types.CallbackQuery):
    _, service, date_label, hour_str = callback.data.split("_", 3)
    hour = int(hour_str)
    today = datetime.now().date()
    dates = {
        "today": today,
        "tomorrow": today + timedelta(days=1),
        "day_after": today + timedelta(days=2)
    }
    selected_date = dates.get(date_label)
    start_time = datetime.combine(selected_date, datetime.min.time().replace(hour=hour))
    end_time = start_time + timedelta(hours=2)  # +2 часа на услугу

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

    # Двойная проверка занятости перед вставкой
    existing = await conn.fetchrow(
        "SELECT id FROM appointments WHERE start_time = $1 AND status IN ('pending', 'approved')", start_time
    )
    if existing:
        await conn.close()
        await callback.message.edit_text("Это время теперь занято. Выберите другое время.")
        return

    await conn.execute(
        """
        INSERT INTO appointments (client_id, service_id, start_time, end_time, status)
        VALUES ($1, $2, $3, $4, 'pending')
        """,
        client_id, service_id, start_time, end_time
    )
    await conn.close()

    await callback.message.edit_text(f"✅ Заявка отправлена!\nУслуга: {service}\nДата: {start_time.strftime('%d.%m.%Y')}\nВремя: {start_time.strftime('%H:%M')}")

    # Уведомление мастеру
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="✅ Подтвердить", callback_data=f"approve_{client_id}_{service_id}_{start_time.strftime('%Y%m%d%H%M%S')}")
    keyboard.button(text="❌ Отклонить", callback_data=f"reject_{client_id}_{service_id}_{start_time.strftime('%Y%m%d%H%M%S')}")
    keyboard.adjust(2)

    await callback.bot.send_message(
        MASTER_ID,
        f"💬 Новая запись:\nКлиент: {full_name}\nУслуга: {service}\nДата: {start_time.strftime('%d.%m.%Y')}\nВремя: {start_time.strftime('%H:%M')}",
        reply_markup=keyboard.as_markup()
    )
