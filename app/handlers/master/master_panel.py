from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.utils.config_loader import MASTER_ID
from app.database import db
import asyncpg

router = Router()

# === Главное меню панели ===
@router.message(Command("panel"))
async def show_panel(message: types.Message):
    if message.from_user.id != int(MASTER_ID):
        return await message.answer("❌ У вас нет доступа к панели мастера.")
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="📋 Мои записи", callback_data="panel_appointments")
    keyboard.button(text="📅 Выходные", callback_data="panel_dayoff")
    keyboard.button(text="♻️ Перенести запись", callback_data="panel_move")
    keyboard.button(text="🎁 Клиенты и баллы", callback_data="panel_clients")
    keyboard.adjust(1)

    await message.answer("🔧 Панель мастера:", reply_markup=keyboard.as_markup())

# === Просмотр всех записей ===
@router.callback_query(lambda c: c.data == "panel_appointments")
async def show_appointments(callback: types.CallbackQuery):
    conn = await asyncpg.connect(db.DATABASE_URL)
    rows = await conn.fetch("SELECT * FROM appointments ORDER BY datetime;")
    await conn.close()

    if not rows:
        return await callback.message.edit_text("📭 Нет записей.")
    
    text = "\n\n".join([
        f"🧍 Клиент ID: {r['client_id']}\n💅 Услуга: {r['service']}\n🕐 Время: {r['datetime']}\n📌 Статус: {r['status']}"
        for r in rows
    ])
    await callback.message.edit_text(f"📋 Текущие записи:\n\n{text}")

# === Выходные ===
@router.callback_query(lambda c: c.data == "panel_dayoff")
async def set_day_off(callback: types.CallbackQuery):
    await callback.message.edit_text("📆 Напиши дату выходного (в формате ГГГГ-ММ-ДД):")

# === Перенос записи ===
@router.callback_query(lambda c: c.data == "panel_move")
async def move_appointment(callback: types.CallbackQuery):
    await callback.message.edit_text("🔁 Напиши ID записи, которую нужно перенести:")

# === Клиенты и бонусы ===
@router.callback_query(lambda c: c.data == "panel_clients")
async def show_clients(callback: types.CallbackQuery):
    conn = await asyncpg.connect(db.DATABASE_URL)
    rows = await conn.fetch("""
        SELECT full_name, points
        FROM clients
        ORDER BY points DESC
        LIMIT 20
    """)
    await conn.close()

    if not rows:
        await callback.message.edit_text("🧾 Клиентов пока нет.")
        return

    text = "🎁 Клиенты и бонусы:\n\n"
    for r in rows:
        text += f"👤 {r['full_name']}\n✨ Баллы: {r['points']}\n\n"

    await callback.message.edit_text(text)
