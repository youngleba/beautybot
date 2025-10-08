# ~/beautybot/app/handlers/master_panel.py
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.utils.db import get_pending_bookings, update_booking_status, get_client_info, add_loyalty_points

router = Router()

MASTER_ID = 456434453  # <-- твой ID мастера


@router.message(Command("master"))
async def cmd_master(message: types.Message):
    if message.from_user.id != MASTER_ID:
        await message.answer("⛔ У вас нет доступа к панели мастера.")
        return

    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Посмотреть заявки", callback_data="view_pending")
    await message.answer("🔧 Панель мастера", reply_markup=builder.as_markup())


@router.callback_query(F.data == "view_pending")
async def view_pending(callback: types.CallbackQuery):
    if callback.from_user.id != MASTER_ID:
        await callback.answer("Нет доступа")
        return

    bookings = await get_pending_bookings()
    if not bookings:
        await callback.message.answer("✅ Нет заявок, ожидающих подтверждения.")
        return

    for b in bookings:
        booking_id = b["id"]
        text = (
            f"🧾 <b>Заявка #{booking_id}</b>\n\n"
            f"👤 Клиент: <code>{b['user_id']}</code>\n"
            f"💅 Услуга: {b['service_name']}\n"
            f"📅 Дата: {b['date']}\n"
            f"⏰ Время: {b['time']}\n"
        )
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Подтвердить", callback_data=f"confirm_{booking_id}")
        builder.button(text="❌ Отклонить", callback_data=f"reject_{booking_id}")
        await callback.message.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("confirm_"))
async def confirm_booking(callback: types.CallbackQuery):
    if callback.from_user.id != MASTER_ID:
        await callback.answer("Нет доступа")
        return

    booking_id = int(callback.data.split("_")[1])
    await callback.answer()

    res = await update_booking_status(booking_id, "confirmed")
    if not res:
        await callback.message.answer("⚠️ Ошибка при обновлении статуса.")
        return

    booking = await get_client_info(booking_id)
    if not booking:
        await callback.message.answer("⚠️ Не удалось найти заявку.")
        return

    user_id = booking["user_id"]
    points_added = await add_loyalty_points(user_id, 50)  # начисляем 50 бонусов

    await callback.message.answer(f"✅ Заявка #{booking_id} подтверждена. Клиенту начислено {points_added} бонусов.")

    try:
        await callback.bot.send_message(
            chat_id=user_id,
            text=f"🎉 Ваша запись #{booking_id} подтверждена!\n💎 Вам начислено {points_added} бонусов."
        )
    except Exception:
        await callback.message.answer("⚠️ Не удалось уведомить клиента (возможно, бот заблокирован).")


@router.callback_query(F.data.startswith("reject_"))
async def reject_booking(callback: types.CallbackQuery):
    if callback.from_user.id != MASTER_ID:
        await callback.answer("Нет доступа")
        return

    booking_id = int(callback.data.split("_")[1])
    await callback.answer()

    res = await update_booking_status(booking_id, "rejected")
    if not res:
        await callback.message.answer("⚠️ Ошибка при обновлении статуса.")
        return

    booking = await get_client_info(booking_id)
    if not booking:
        await callback.message.answer("⚠️ Не удалось найти заявку.")
        return

    user_id = booking["user_id"]
    await callback.message.answer(f"❌ Заявка #{booking_id} отклонена.")

    try:
        await callback.bot.send_message(
            chat_id=user_id,
            text=f"😔 Ваша запись #{booking_id} была отклонена. Пожалуйста, выберите другое время."
        )
    except Exception:
        await callback.message.answer("⚠️ Не удалось уведомить клиента (возможно, бот заблокирован).")

