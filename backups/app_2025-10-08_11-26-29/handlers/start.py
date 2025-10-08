# ~/beautybot/app/handlers/start.py
from aiogram import Router, types
from aiogram.filters import Command
from app.utils.db import get_services, create_booking

router = Router()

# /start — приветствие
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    services = await get_services()
    if not services:
        await message.answer("😔 Пока нет доступных услуг.")
        return

    keyboard = types.InlineKeyboardMarkup()
    for s in services:
        keyboard.add(
            types.InlineKeyboardButton(
                text=f"{s['name']} — {s['price']}₽ ({s['duration']} мин)",
                callback_data=f"service_{s['id']}"
            )
        )
    await message.answer("💅 Привет! Выбери услугу для записи:", reply_markup=keyboard)


# Пользователь выбирает услугу
@router.callback_query(lambda c: c.data.startswith("service_"))
async def select_service(callback: types.CallbackQuery):
    service_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

    booking_id = await create_booking(user_id, service_id)
    if booking_id:
        await callback.message.answer(
            "📅 Ваша заявка создана и ожидает подтверждения мастера!"
        )
    else:
        await callback.message.answer("⚠️ Ошибка при создании заявки.")
    await callback.answer()

