import logging
from aiogram import Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncpg
from datetime import datetime, timedelta
from app.utils.config_loader import DATABASE_URL, MASTER_ID

def register_panel_handlers(dp: Dispatcher):
    """Регистрация обработчиков для панели мастера."""
    dp.register_message_handler(show_panel, commands='panel')
    dp.register_callback_query_handler(approve_from_panel, lambda c: c.data.startswith('panel_approve_'))
    dp.register_callback_query_handler(reject_from_panel, lambda c: c.data.startswith('panel_reject_'))
    dp.register_callback_query_handler(choose_date_transfer, lambda c: c.data.startswith('panel_transfer_date_'))
    dp.register_callback_query_handler(confirm_transfer, lambda c: c.data.startswith('panel_transfer_time_'))

async def show_panel(message: types.Message):
    """Показать список всех записей для мастера."""
    if message.from_user.id != MASTER_ID:
        await message.reply("❌ Доступ только для мастера.")
        return
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        rows = await conn.fetch("""
            SELECT a.id, c.full_name, s.name as service_name, a.date, a.time, a.confirmed, a.duration
            FROM appointments a
            JOIN clients c ON a.user_id = c.id
            JOIN services s ON a.service_id = s.id
            WHERE a.date >= CURRENT_DATE - INTERVAL '1 day'
            ORDER BY a.date ASC, a.time ASC
        """)
        await conn.close()
        if not rows:
            await message.reply("📋 Нет записей.")
            return

        await message.reply("🏢 Панель управления. Список записей:")
        for row in rows:
            status = "✅ Одобрена" if row['confirmed'] else "⏳ Ожидает"
            duration = row['duration'] or 120
            text = (
                f"📋 ID: {row['id']}\n"
                f"Клиент: {row['full_name']}\n"
                f"Услуга: {row['service_name']}\n"
                f"Дата: {row['date'].strftime('%d.%m.%Y')}\n"
                f"Время: {row['time']}\n"
                f"Длительность: {duration} мин\n"
                f"Статус: {status}"
            )
            keyboard = InlineKeyboardMarkup(row_width=3)
            btn_approve = InlineKeyboardButton("✅ Одобрить" if not row['confirmed'] else "🔄 Сброс", callback_data=f"panel_approve_{row['id']}")
            btn_reject = InlineKeyboardButton("❌ Отклонить" if not row['confirmed'] else "🗑️ Удалить", callback_data=f"panel_reject_{row['id']}")
            btn_transfer = InlineKeyboardButton("📅 Перенести", callback_data=f"panel_transfer_{row['id']}")
            keyboard.add(btn_approve, btn_reject, btn_transfer)
            await message.reply(text, reply_markup=keyboard)
        await message.reply("Конец списка. Используйте /panel для обновления.")
    except Exception as err:
        logging.error(f"Ошибка в show_panel: {err}")
        await message.reply("❗ Ошибка загрузки записей.")

async def approve_from_panel(callback: types.CallbackQuery):
    """Подтвердить запись из панели."""
    if callback.from_user.id != MASTER_ID:
        await callback.answer("❌ Нет доступа.")
        return
    appointment_id = int(callback.data.split('_')[-1])
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        updated = await conn.execute(
            "UPDATE appointments SET confirmed = true WHERE id = $1", appointment_id
        )
        if "UPDATE 0" in updated:
            await callback.answer("❗ Запись не найдена.")
            return
        # Уведомление клиенту
        client_row = await conn.fetchrow(
            "SELECT user_id, date, time, s.name as service FROM appointments a JOIN services s ON a.service_id = s.id WHERE a.id = $1", appointment_id
        )
        if client_row:
            await callback.bot.send_message(
                client_row['user_id'],
                f"🎉 Ваша запись {client_row['service']} на {client_row['date'].strftime('%d.%m.%Y')} в {client_row['time']} подтверждена!"
            )
        await conn.close()
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.reply(f"✅ Запись {appointment_id} подтверждена.")
    except Exception as err:
        logging.error(f"Ошибка approve_from_panel: {err}")
        await callback.answer("❗ Ошибка.")
    await callback.answer()

async def reject_from_panel(callback: types.CallbackQuery):
    """Отклонить/удалить запись из панели."""
    if callback.from_user.id != MASTER_ID:
        await callback.answer("❌ Нет доступа.")
        return
    appointment_id = int(callback.data.split('_')[-1])
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        # Удаляем только не подтверждённые, или все для мастера
        deleted = await conn.execute(
            "DELETE FROM appointments WHERE id = $1", appointment_id
        )
        if "DELETE 0" in deleted:
            await callback.answer("❗ Запись не найдена.")
            return
        # Уведомление клиенту, если была
        client_row = await conn.fetchrow("SELECT user_id FROM appointments WHERE id = $1", appointment_id)
        if client_row:
            await callback.bot.send_message(
                client_row['user_id'], "😔 Ваша запись отклонена мастером."
            )
        await conn.close()
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.reply(f"❌ Запись {appointment_id} отклонена.")
    except Exception as err:
        logging.error(f"Ошибка reject_from_panel: {err}")
        await callback.answer("❗ Ошибка.")
    await callback.answer()

async def choose_date_transfer(callback: types.CallbackQuery):
    """Выбор даты для переноса."""
    if callback.from_user.id != MASTER_ID:
        await callback.answer("❌ Нет доступа.")
        return
    appointment_id = int(callback.data.split('_')[-1])
    today = datetime.now().date()
    keyboard = InlineKeyboardMarkup(row_width=1)
    for i in range(7):  # 7 дней вперёд
        new_date = today + timedelta(days=i)
        date_key = new_date.strftime('%Y%m%d')
        keyboard.add(InlineKeyboardButton(new_date.strftime('%d.%m.%Y'), callback_data=f"panel_transfer_time_{appointment_id}_{date_key}"))
    await callback.message.edit_text(
        f"📅 Перенос записи {appointment_id}. Выберите новую дату:",
        reply_markup=keyboard
    )
    await callback.answer()

async def confirm_transfer(callback: types.CallbackQuery):
    """Подтверждение переноса с выбором времени."""
    if callback.from_user.id != MASTER_ID:
        await callback.answer("❌ Нет доступа.")
        return
    parts = callback.data.split('_')
    appointment_id = int(parts[-2])
    new_date_key = parts[-1]
    new_date = datetime.strptime(new_date_key, '%Y%m%d').date()
    keyboard = InlineKeyboardMarkup(row_width=2)
    for hour in range(9, 18):  # 9-18:00
        time_str = f"{hour:02d}:00"
        keyboard.add(InlineKeyboardButton(time_str, callback_data=f"panel_confirm_final_{appointment_id}_{new_date_key}_{time_str}"))
    await callback.message.edit_text(
        f"⏰ Для записи {appointment_id} на {new_date.strftime('%d.%m.%Y')} выберите время:",
        reply_markup=keyboard
    )
    await callback.answer()

dp.register_callback_query_handler(final_confirm_transfer, lambda c: c.data.startswith('panel_confirm_final_'))

async def final_confirm_transfer(callback: types.CallbackQuery):
    """Финальный перенос записи."""
    if callback.from_user.id != MASTER_ID:
        await callback.answer("❌ Нет доступа.")
        return
    parts = callback.data.split('_')
    appointment_id = int(parts[-4])
    new_date_key = parts[-3]
    new_time = parts[-1]
    new_date = datetime.strptime(new_date_key, '%Y%m%d').date()
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        # Получаем старые данные
        old_row = await conn.fetchrow(
            "SELECT user_id, date, time, service_id FROM appointments WHERE id = $1", appointment_id
        )
        if not old_row:
            await callback.answer("❗ Запись не найдена.")
            return
        # Обновляем
        await conn.execute(
            """
            UPDATE appointments SET date = $1, time = $2 WHERE id = $3
            """,
            new_date, new_time, appointment_id
        )
        await conn.close()
        # Уведомление клиенту
        await callback.bot.send_message(
            old_row['user_id'],
            f"📅 Ваша запись перенесена!\nС {old_row['date'].strftime('%d.%m.%Y')} {old_row['time']} "
            f"на {new_date.strftime('%d.%m.%Y')} {new_time}."
        )
        await callback.message.edit_text(f"✅ Запись {appointment_id} перенесена на {new_date.strftime('%d.%m.%Y')} {new_time}.")
    except Exception as err:
        logging.error(f"Ошибка final_confirm_transfer: {err}")
        await callback.answer("❗ Ошибка переноса.")
    await callback.answer()
