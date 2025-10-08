# ~/beautybot/app/handlers/master_panel.py
from aiogram import Router, types
from aiogram.filters import Command
from app.utils.db import get_unconfirmed_bookings, update_booking_status

router = Router()

# Панель мастера
@router.message(Command("panel"))
async def master_panel(message: types.Message):
    bookings = await get_unconfirmed_bookings()
    if not bookings:
        await message.answer("🕓 Нет новых заявок на подтверждение.")
        return

    for b in bookings:
        text = (
            f"💅 Заявка #{b['id']}\n"
            f"Клиент: {b['user_id']}\n"
            f"Услуга: {b['service_name']}\n"
            f"Дата: {b['date']}\n"
            f"Время: {b['time']}"
        )

        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("✅ Подтвердить", callback_data=f"approve_{b['id']}"),
            types.InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{b['id']}")
        )

        await message.answer(text, reply_markup=keyboard)


# Обработка подтверждения / отклонения
@router.callback_query(lambda c: c.data.startswith(("approve_", "reject_")))
async def process_decision(callback: types.CallbackQuery):
    action, booking_id = callback.data.split("_")
    new_status = "approved" if action == "approve" else "rejected"

    await update_booking_status(int(booking_id), new_status)
    await callback.message.edit_text(
        f"Заявка #{booking_id} — {'✅ подтверждена' if action == 'approve' else '❌ отклонена'}"
    )
    await callback.answer()

