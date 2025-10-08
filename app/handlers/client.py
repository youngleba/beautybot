from aiogram import Router, types, F
from app.utils.db import get_services, get_client_points, get_bookings_by_user

router = Router()

# ---------- Показ услуг ----------
@router.message(F.text.in_({"📅 Записаться", "💅 Записаться", "Записаться"}))
async def show_services(message: types.Message):
    services = await get_services()
    if not services:
        await message.answer("😔 Пока нет доступных услуг.")
        return

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[])
    for s in services:
        keyboard.inline_keyboard.append([
            types.InlineKeyboardButton(
                text=f"{s['name']} — {s['price']}₽ ({s['duration']} мин)",
                callback_data=f"service_{s['id']}"
            )
        ])

    await message.answer("✨ Выберите услугу:", reply_markup=keyboard)

# ---------- Бонусы ----------
@router.message(F.text == "💎 Мои бонусы")
async def my_points(message: types.Message):
    user_id = message.from_user.id
    points = await get_client_points(user_id)
    await message.answer(f"💰 У вас {points} бонусных баллов.")

# ---------- Мои записи ----------
@router.message(F.text == "📖 Мои записи")
async def my_bookings(message: types.Message):
    user_id = message.from_user.id
    bookings = await get_bookings_by_user(user_id)
    if not bookings:
        await message.answer("📭 У вас пока нет записей.")
        return

    text = "🗓 Ваши записи:\n\n"
    for b in bookings:
        text += (
            f"🔹 <b>{b['service_name']}</b>\n"
            f"📅 Дата: {b['date']}\n"
            f"⏰ Время: {b['time_start']} – {b['time_end']}\n"
            f"💬 Статус: {b['status']}\n\n"
        )
    await message.answer(text, parse_mode="HTML")
