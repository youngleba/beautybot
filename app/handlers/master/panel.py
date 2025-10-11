import logging
from aiogram import Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncpg
from datetime import datetime, timedelta
from app.utils.config_loader import DATABASE_URL, MASTER_ID

def register_panel_handlers(dp: Dispatcher):
    dp.register_message_handler(show_panel, commands="panel")
    dp.register_callback_query_handler(approve_from_panel, lambda c: c.data.startswith('panel_approve_'))
    dp.register_callback_query_handler(reject_from_panel, lambda c: c.data.startswith('panel_reject_'))
    dp.register_callback_query_handler(transfer_appointment, lambda c: c.data.startswith('panel_transfer_'))

async def show_panel(message: types.Message):
    if message.from_user.id != MASTER_ID:
        await message.reply("❌ Доступ только для мастера.")
        return
    await message.reply("🏢 Панель управления записями.\nЗагружаю список...")
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        rows = await conn.fetch("""
            SELECT a.id, c.full_name, s.name as service_name, a.date, a.time, a.confirmed, a.duration
            FROM appointments a
            JOIN clients c ON a.user_id = c.id
            JOIN services s ON a.service_id = s.id
            WHERE a.date >= CURRENT_DATE - INTERVAL '1 day' OR (a.date < CURRENT_DATE AND a.confirmed = true)
            ORDER BY a.date ASC, a.time ASC
        """)
        if not rows:
            await message.reply("📋 Нет записей.")
            return
        keyboard = InlineKeyboardMarkup(row_width=3)
        for row in rows:
            status = "✅ Одобрена" if row['confirmed'] else "⏳ Ожидает"
            btn_approve = InlineKeyboardButton("✅" if not row['confirmed'] else "❌ Отменить", callback_data=f"panel_approve_{row['id']}")
            btn_reject = InlineKeyboardButton("❌ Откл" if not row['confirmed'] else "-", callback_data=f"panel_reject_{row['id']}")
            btn_transfer = InlineKeyboardButton("Перен", callback_data=f"panel_transfer_{row['id']}")
            keyboard.add(btn_approve, btn_reject, btn_transfer)
            await message.reply(
                f"📋 Запись ID {row['id']}:\nКлиент: {row['full_name']}\nУслуга: {row['service_name']}\nДата: {row['date'].strftime('%d.%m.%Y')}\nВремя: {row['time']}\n{getattr(row, 'duration', 120)} мин\nСтатус: {status}",
                reply_markup=InlineKeyboardMarkup().add(btn_approve, btn_reject, btn_transfer)
            )
        await message.reply("Все записи загружены.", reply_markup=keyboard)
    finally:
        await conn.close()

async def approve_from_panel(callback: types.CallbackQuery):
    if callback.from_user.id != MASTER_ID:
        await callback.answer("❌ Нет доступа.")
        return
    appointment_id = int(callback.data.split('_')[2])
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        updated = await conn.execute(
            "UPDATE appointments SET confirmed = true WHERE id = $1", appointment_id
        )
        if "UPDATE 0" in updated:
            await callback.message.edit_text("❗ Запись не найдена.")
            return
        row = await conn.fetchrow(
            "SELECT user_id FROM appointments WHERE id = $1", appointment_id
        )
        await callback.bot.send_message(
            row['user_id'], "🎉 Ваша запись подтверждена!\nМастер утвердил."
        )
        await callback.message.edit_text(f"✅ Запись {appointment_id} подтверждена.")
    finally:
        await conn.close()
    await callback.answer()

async def reject_from_panel(callback: types.CallbackQuery):
    if callback.from_user.id != MASTER_ID:
        await callback.answer("❌ Нет доступа.")
        return
    appointment_id = int(callback.data.split('_')[2])
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        deleted = await conn.execute(
            "DELETE FROM appointments WHERE id = $1 AND confirmed = false", appointment_id
        )
        if "DELETE 0" in deleted:
            await callback.message.edit_text("❗ Запись уже обработана.")
            return
        row = await conn.fetchrow(
            "SELECT user_id FROM appointments WHERE id = $1", appointment_id
        )
        if row:
            await callback.bot.send_message(
                row['user_id'], "😔 Ваша запись отклонена мастером."
            )
        await callback.message.edit_text(f"❌ Запись {appointment_id} отклонена.")
    finally:
        await conn.close()
    await callback.answer()

async def transfer_appointment(callback: types.CallbackQuery):
    if callback.from_user.id != MASTER_ID:
        await callback.answer("❌ Нет доступа.")
        return
    appointment_id = int(callback.data.split('_')[2])
    keyboard = InlineKeyboardMarkup(row_width=2)
    today = datetime.now().date()
    dates = [(today + timedelta(days=i), ".strptime('%Y-%m%d")".format(date=str((today + timedelta(days=i)).strftime('%Y%m%d')))]) for i in range(5)]
    for d, date_str in dates:
        keyboard.add(InlineKeyboardButton(d.strftime('%d.%m.%Y'), callback_data=f"panel_transfer_date_{appointment_id}_{date_str}"))
    times = [f"{h}:00" for h in range(9, 17)]
    for t in times:
        keyboard.add(InlineKeyboardButton(t, callback_data=f"panel_confirm_transfer_{appointment Nearest_id}_{t}"))
    await callback.message.edit_text(
        f"📅 Перенос записи {appointment_id}. Выберите дату и время:",
        reply_markup=keyboard
    )
    await callback.answer()

# Расширить если нужно, но базовый готов.
