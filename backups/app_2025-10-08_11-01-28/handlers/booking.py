# ~/beautybot/app/handlers/booking.py
from aiogram import Router, types
from aiogram.filters import Command
from app.utils.db import get_services, create_booking

router = Router()

# Показываем список услуг
@router.message(Command("book"))
async def cmd_book(message: types.Message):
    services = await get_services()
    if not services:
        await message.answer("Пока нет доступных услуг.")
        return

    keyboard = types.InlineKeyboardMarkup()
    for s in services:
        keyboard.add(
            types.InlineKeyboardButton(
                text=f"{s['name']} — {s['price']}₽ ({s['duration']} мин)",
                callback_data=f"service_{s['id']}"
            )
        )
    await message.answer("💅 Выберите услугу:", reply_markup=keyboard)


# Обработка выбора услуги
@router.callback_query(lambda c: c.data.startswith("service_"))
async def select_service(callback: types.CallbackQuery):
    service_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

    booking_id = await create_booking(user_id, service_id)
    await callback.message.answer(
        f"✅ Ваша запись создана!\nID брони: {booking_id}\nМастер подтвердит время записи в ближайшее время."
    )
    await callback.answer()

