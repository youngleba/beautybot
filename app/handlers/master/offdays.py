from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import asyncpg
from datetime import datetime, timedelta
from app.utils.config_loader import DATABASE_URL, MASTER_ID

router = Router()

@router.message(Command("offdays"))
async def manage_offdays(message: types.Message):
    if message.from_user.id != MASTER_ID:
        await message.answer("❌ Нет доступа")
        return
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Добавить выходной (завтра)", callback_data="add_offday")
    keyboard.button(text="Показать выходные", callback_data="show_offdays")
    keyboard.adjust(1)
    await message.answer("Управление выходными:", reply_markup=keyboard.as_markup())

@router.callback_query(F.data == "add_offday")
async def add_offday(callback: types.CallbackQuery):
    tomorrow = datetime.now().date() + timedelta(days=1)
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        await conn.execute("INSERT INTO master_off_days(day) VALUES($1) ON CONFLICT DO NOTHING", tomorrow)
        await conn.close()
        await callback.answer(f"Добавлен выходной: {tomorrow.strftime('%d.%m.%Y')}")
    except Exception as e:
        await callback.answer("Ошибка при добавлении выходного.")
    # Обновляем меню после добавления
    await manage_offdays(await callback.message.answer(""))

@router.callback_query(F.data == "show_offdays")
async def show_offdays(callback: types.CallbackQuery):
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        rows = await conn.fetch("SELECT day FROM master_off_days ORDER BY day")
        await conn.close()
        if not rows:
            await callback.message.answer("Выходных нет.")
            return
        text = "📅 Выходные мастера:\n"
        for row in rows:
            text += f" - {row['day'].strftime('%d.%m.%Y')}\n"
        await callback.message.answer(text)
    except Exception as e:
        await callback.message.answer("Ошибка при получении списка выходных.")
