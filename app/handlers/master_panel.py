from aiogram import Router, types, F
from aiogram.filters import Command
import os

from app.utils.db import update_booking_status, get_client_info, get_pending_bookings

router = Router()
MASTER_ID = int(os.getenv("MASTER_ID", "456434453"))

# Команда мастера: показать pending брони
@router.message(Command("master"))
async def master_menu(message: types.Message):
    if message.from_user.id != MASTER_ID:
        await message.answer("❌ У вас нет доступа к этой команде.")
        return

    pending = await get_pending_bookings()
    if not pending:
        await message.answer("Нет ожидающих заявок.")
        return

    for b in pending:
        text = f"#{b['id']} — Клиент: {b.get('client_name') or b.get('user_id')}\nУслуга: {b.get('service_name')}\n📅 {b.get('date')} ⏰ {b.get('time')}\nСтатус: {b.get('status')}"
        kb = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm:{b['id']}"),
                    types.InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject:{b['id']}")
                ]
            ]
        )
        await message.answer(text, reply_markup=kb)


# Callback: мастер подтвердил бронь
@router.callback_query(F.data.startswith("confirm:"))
async def on_confirm(cb: types.CallbackQuery):
    booking_id = int(cb.data.split(":", 1)[1])
    ok = await update_booking_status(booking_id, "confirmed")
    if ok:
        info = await get_client_info(booking_id)
        if info:
            try:
                await cb.bot.send_message(info.get("user_id"), f"✅ Ваша запись #{booking_id} подтверждена мастером.\n📅 {info.get('date')} ⏰ {info.get('time')}")
            except Exception:
                pass
        await cb.message.edit_text(f"✅ Подтвержено (#{booking_id})")
        await cb.answer("Подтвержено")
    else:
        await cb.answer("Ошибка при подтверждении", show_alert=True)


# Callback: мастер отклонил бронь
@router.callback_query(F.data.startswith("reject:"))
async def on_reject(cb: types.CallbackQuery):
    booking_id = int(cb.data.split(":", 1)[1])
    ok = await update_booking_status(booking_id, "rejected")
    if ok:
        info = await get_client_info(booking_id)
        if info:
            try:
                await cb.bot.send_message(info.get("user_id"), f"❌ Ваша запись #{booking_id} отклонена мастером.")
            except Exception:
                pass
        await cb.message.edit_text(f"❌ Отклонено (#{booking_id})")
        await cb.answer("Отклонено")
    else:
        await cb.answer("Ошибка при отклонении", show_alert=True)
