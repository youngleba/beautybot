from aiogram import Router, types, F
from aiogram.filters import Command
from app.utils.config_loader import MASTER_ID
from app.database import db

router = Router()

@router.message(Command("panel"))
async def show_panel(message: types.Message):
    if message.from_user.id != MASTER_ID:
        return await message.answer("❌ У вас нет доступа к панели мастера.")
    
    keyboard = [
        [types.KeyboardButton(text="📋 Мои записи")],
        [types.KeyboardButton(text="📅 Выходные")],
        [types.KeyboardButton(text="♻️ Перенести запись")],
    ]
    markup = types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
    await message.answer("🔧 Панель мастера:", reply_markup=markup)

@router.message(F.text == "📋 Мои записи")
async def view_appointments(message: types.Message):
    if message.from_user.id != MASTER_ID:
        return
    conn = await db.asyncpg.connect(db.DATABASE_URL)
    rows = await conn.fetch("SELECT * FROM appointments ORDER BY datetime;")
    await conn.close()
    if not rows:
        return await message.answer("📭 Нет записей.")
    text = "\n\n".join([
        f"🧍 Клиент: {r['client_id']}\n💅 Услуга: {r['service']}\n🕐 Время: {r['datetime']}\n📌 Статус: {r['status']}"
        for r in rows
    ])
    await message.answer(f"📋 Текущие записи:\n\n{text}")

@router.message(F.text == "📅 Выходные")
async def set_day_off(message: types.Message):
    if message.from_user.id != MASTER_ID:
        return
    await message.answer("📆 Напиши дату выходного (в формате ГГГГ-ММ-ДД):")

@router.message(F.text == "♻️ Перенести запись")
async def move_appointment(message: types.Message):
    if message.from_user.id != MASTER_ID:
        return
    await message.answer("🔁 Напиши ID записи, которую нужно перенести:")
