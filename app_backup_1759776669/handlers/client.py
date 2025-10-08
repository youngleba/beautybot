# ~/beautybot/app/handlers/client.py
from aiogram import Router, types, F
from aiogram.filters import Command
from app.utils.db import get_services, create_booking
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

router = Router()

@router.message(F.text == "📅 Записаться")
async def show_services(message: types.Message):
    """
    Показывает список услуг, доступных для записи.
    """
    services = await get_services()
    if not services:
        await message.answer("⚠️ Пока нет доступных услуг.")
        return

    keyboard = InlineKeyboardMarkup(row_width=1)
    for s in services:
        btn = InlineKeyboardButton(
            text=f"{s['name']} — {s['price']}₽ ({s['duration']} мин)",
            callback_data=f"book_service_{s['id']}"
        )
        keyboard.add(btn)

    await message.answer("💅 Выбери услугу:", reply_markup=keyboard)


@router.callback_query(F.data.startswith("book_service_"))
async def handle_booking(callback: types.CallbackQuery):
    """
    Обрабатывает выбор услуги и создаёт бронь в базе.
    """
    service_id = int(callback.data.replace("book_service_", ""))
    user_id = callback.from_user.id

    booking_id = await create_booking(user_id, service_id)
    if not booking_id:
        await callback.message.answer("⚠️ Ошибка при создании записи.")
        await callback.answer()
        return

    await callback.message.answer("✅ Заявка отправлена мастеру. Ожидайте подтверждения.")
    await callback.answer()

