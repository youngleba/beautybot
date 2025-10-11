import logging
from aiogram import Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncpg
from datetime import datetime, timedelta
from app.utils.config_loader import DATABASE_URL, MASTER_ID

def register_booking_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(book_start, lambda c: c.data == 'book_start')
    dp.register_callback_query_handler(choose_date, lambda c: c.data.startswith('service_'))
    dp.register_callback_query_handler(choose_time, lambda c: c.data.startswith('date_'))
    dp.register_callback_query_handler(confirm_booking, lambda c: c.data.startswith('time_'))

async def book_start(callback: types.CallbackQuery):
    try:
        keyboard = InlineKeyboardMarkup(row_width=1)
        services = ["Маникюр", "Стрижка", "Массаж"]
        for service in services:
            keyboard.add(InlineKeyboardButton(service, callback_data=f"service_{service}"))
        await callback.message.edit_text(
            "Выбери услугу:", reply_markup=keyboard
        )
    except Exception as err:
        logging.error(f"Ошибка в book_start: {err}")
        await callback.message.edit_text("❗ Произошла ошибка, попробуйте позже.")

async def choose_date(callback: types.CallbackQuery):
    try:
        service = callback.data.split("_", 1)[1]
        keyboard = InlineKeyboardMarkup(row_width=1)
        today = datetime.now().date()
        dates = {
            "today": today,
            "tomorrow": today + timedelta(days=1),
            "day_after": today + timedelta(days=2)
        }
        for label, date in dates.items():
            keyboard.add(InlineKeyboardButton(date.strftime("%d.%m.%Y"), callback_data=f"date_{service}_{label}"))
        await callback.message.edit_text(
            f"Выбрана услуга: {service}\nТеперь выбери дату:",
            reply_markup=keyboard
        )
    except Exception as err:
        logging.error(f"Ошибка в choose_date: {err}")
        await callback.message.edit_text("❗ Произошла ошибка, попробуйте позже.")

async def choose_time(callback: types.CallbackQuery):
    try:
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
        logging.info(f"Выбор времени для даты {selected_date} и услуги {service}")
        conn = await asyncpg.connect(DATABASE_URL)
        try:
            rows = await conn.fetch(
                """
                SELECT date, time, duration FROM appointments
                WHERE date = $1 AND confirmed = true
                """,
                selected_date
            )
            logging.info(f"Получено {len(rows)} занятых записей для {selected_date}")
        except Exception as db_err:
            logging.error(f"Ошибка запроса к БД: {db_err}")
            await callback.message.edit_text("❗ Ошибка БД, попробуйте позже.")
            return
        finally:
            await conn.close()
        busy_times = set()
        for row in rows:
            start_hour = row['time'].hour if row['time'] else 0
            duration = row['duration'] or 120  # минуты
            end_hour = start_hour + (duration // 60)
            for hour in range(start_hour, end_hour):
                busy_times.add(hour)
        all_times = {8, 9, 10, 11, 12, 13, 14, 15, 16, 17}
        free_times = all_times - busy_times
        if not free_times:
            await callback.message.edit_text(
                "На эту дату все время занято. Выберите другую дату или услугу."
            )
            return
        keyboard = InlineKeyboardMarkup(row_width=2)
        for hour in sorted(free_times):
            time_str = f"{hour:02d}:00"
            keyboard.add(InlineKeyboardButton(time_str, callback_data=f"time_{service}_{date_label}_{hour}"))
        await callback.message.edit_text(
            f"Выбрана услуга: {service}\nДата: {selected_date.strftime('%d.%m.%Y')}\nСвободное время:",
            reply_markup=keyboard
        )
    except Exception as err:
        logging.error(f"Ошибка в choose_time: {err}")
        await callback.message.edit_text("❗ Произошла ошибка, попробуйте позже.")

async def confirm_booking(callback: types.CallbackQuery):
    try:
        _, service, date_label, hour_str = callback.data.split("_", 3)
        hour = int(hour_str)
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
        time_obj = datetime.min.time().replace(hour=hour)
        duration = 120  # минуты по умолчанию
        client_id = callback.from_user.id
        username = callback.from_user.username or ""
        full_name = callback.from_user.full_name or username
        conn = await asyncpg.connect(DATABASE_URL)
        try:
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
                    "INSERT INTO services (name, duration_minutes) VALUES ($1, $2)", service, duration
                )
                service_id_row = await conn.fetchrow(
                    "SELECT id FROM services WHERE name=$1", service
                )
            service_id = service_id_row['id']
            # Проверка занятости по date/time
            existing = await conn.fetchrow(
                "SELECT id FROM appointments WHERE date = $1 AND time = $2 AND confirmed = true",
                selected_date, time_obj
            )
            if existing:
                await callback.message.edit_text(
                    "❗ Это время уже занято. Пожалуйста, выберите другое."
                )
                return
            await conn.execute(
                """
                INSERT INTO appointments (user_id, service_id, date, time, duration, confirmed)
                VALUES ($1, $2, $3, $4, $5, false)
                """,
                client_id, service_id, selected_date, time_obj, duration
            )
        finally:
            await conn.close()
        await callback.message.edit_text(
            f"✅ Заявка отправлена мастеру!\nУслуга: {service}\nДата: {selected_date.strftime('%d.%m.%Y')}\nВремя: {time_str}"
        )
        # Кнопки для мастера (confirmed = false как pending)
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(InlineKeyboardButton(
            "✅ Подтвердить", callback_data=f"approve_{client_id}_{service_id}_{selected_date.strftime('%Y%m%d')}_{hour:02d}"
        ))
        keyboard.add(InlineKeyboardButton(
            "❌ Отклонить", callback_data=f"reject_{client_id}_{service_id}_{selected_date.strftime('%Y%m%d')}_{hour:02d}"
        ))
        await callback.bot.send_message(
            MASTER_ID,
            f"💬 Новая запись:\nКлиент: {full_name}\nУслуга: {service}\nДата: {selected_date.strftime('%d.%m.%Y')}\nВремя: {hour:02d}:00",
            reply_markup=keyboard
        )
    except Exception as err:
        logging.error(f"Ошибка в confirm_booking: {err}")
        await callback.message.edit_text("❗ Ошибка при оформлении записи, попробуйте позже.")
