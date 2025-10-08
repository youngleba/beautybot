# ~/beautybot/main.py
import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from dotenv import load_dotenv

from app.handlers.master_panel import router as master_router
from app.utils.db import init_db, create_booking, get_bookings_by_user

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Подключаем роутеры
dp.include_router(master_router)

@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer(
        "👋 Привет! Это бот для записи к мастеру.\n"
        "Используй /book чтобы создать запись, или /mybookings чтобы посмотреть свои записи."
    )

@dp.message(Command("book"))
async def book_handler(message: Message):
    # Для теста создаём бронь вручную
    booking_id = await create_booking(
        user_id=message.from_user.id,
        service_id=1,
        date_str="2025-10-10",
        time_str="12:00"
    )
    if booking_id:
        await message.answer(f"✅ Запись #{booking_id} создана! Ожидает подтверждения мастера.")
        # Отправляем мастеру подтверждение (для теста — тебе же)
        await bot.send_message(
            message.from_user.id,
            f"📩 Новая заявка #{booking_id}\nПодтвердить?",
            reply_markup=types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        types.InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_{booking_id}"),
                        types.InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{booking_id}")
                    ]
                ]
            )
        )
    else:
        await message.answer("⚠️ Ошибка при создании записи.")

@dp.message(Command("mybookings"))
async def my_bookings_handler(message: Message):
    bookings = await get_bookings_by_user(message.from_user.id)
    if not bookings:
        await message.answer("📭 У вас пока нет записей.")
        return

    text = "📅 Ваши записи:\n\n"
    for b in bookings:
        text += f"#{b['id']} — {b['date']} {b['time']} ({b['status']})\n"
    await message.answer(text)

async def main():
    await init_db()
    await dp.start_polling(bot, handle_signals=False)

if __name__ == "__main__":
    asyncio.run(main())

