from aiogram import Router, types, F
from aiogram.filters import Command
from datetime import datetime, date
import calendar
import os

from app.utils.db import get_services, create_booking
from app.database.schedule import get_master_schedule

router = Router()

# MASTER ID (по умолчанию тот id, который ты ранее дал; можно переопределить через .env)
MASTER_ID = int(os.getenv("MASTER_ID", "456434453"))

# Команда /book и текстовая кнопка "Записаться"
@router.message(Command("book"))
@router.message(F.text == "Записаться")
async def cmd_book(message: types.Message):
    services = await get_services()
    if not services:
        await message.answer("Пока нет доступных услуг.")
        return

    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text=s["name"], callback_data=f"svc:{s['id']}")]
            for s in services
        ]
    )
    await message.answer("💅 Выберите услугу:", reply_markup=kb)


# Выбрали услугу -> показываем месяцы (текущий и следующий)
@router.callback_query(F.data.startswith("svc:"))
async def on_service_selected(cb: types.CallbackQuery):
    svc_id = cb.data.split(":", 1)[1]
    now = datetime.now()
    year1, mon1 = now.year, now.month
    # next month calc
    if mon1 == 12:
        year2, mon2 = year1 + 1, 1
    else:
        year2, mon2 = year1, mon1 + 1

    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text=f"{date(year1, mon1, 1).strftime('%B %Y')}", callback_data=f"mon:{year1}-{mon1}:{svc_id}")],
            [types.InlineKeyboardButton(text=f"{date(year2, mon2, 1).strftime('%B %Y')}", callback_data=f"mon:{year2}-{mon2}:{svc_id}")]
        ]
    )
    await cb.message.answer("Выберите месяц:", reply_markup=kb)
    await cb.answer()


# Выбран месяц -> показываем все дни в этом месяце
@router.callback_query(F.data.startswith("mon:"))
async def on_month_selected(cb: types.CallbackQuery):
    payload = cb.data.split(":", 2)[1]  # "YYYY-M"
    svc_id = cb.data.split(":", 2)[2]
    year_s, mon_s = payload.split("-")
    year = int(year_s); mon = int(mon_s)
    _, last_day = calendar.monthrange(year, mon)

    rows = []
    # создаём кнопки по 7 в ряд
    row = []
    for d in range(1, last_day + 1):
        date_str = f"{year:04d}-{mon:02d}-{d:02d}"
        row.append(types.InlineKeyboardButton(text=str(d), callback_data=f"day:{date_str}:{svc_id}"))
        if len(row) == 7:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    # Добавляем кнопку назад к выбору услуг
    rows.append([types.InlineKeyboardButton(text="◀ Назад к услугам", callback_data="show_services")])

    kb = types.InlineKeyboardMarkup(inline_keyboard=rows)
    await cb.message.answer(f"Выберите день — {date(year, mon, 1).strftime('%B %Y')}", reply_markup=kb)
    await cb.answer()


# Выбран день -> показываем слоты с get_master_schedule (шаг 2 часа)
@router.callback_query(F.data.startswith("day:"))
async def on_day_selected(cb: types.CallbackQuery):
    _, date_str, svc_id = cb.data.split(":", 2)
    # date_str = "YYYY-MM-DD"
    # получаем слоты
    try:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        await cb.answer("Неправильная дата.", show_alert=True)
        return

    slots = await get_master_schedule(selected_date, master_id=1)
    if not slots:
        await cb.message.answer("Нет свободных слотов на выбранный день.")
        await cb.answer()
        return

    # формируем кнопки по 3 в ряд
    rows = []
    row = []
    for s in slots:
        t = s.get("time")
        # callback: time:YYYY-MM-DD:HH:MM:svc_id
        row.append(types.InlineKeyboardButton(text=t, callback_data=f"time:{date_str}:{t}:{svc_id}"))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    # назад
    rows.append([types.InlineKeyboardButton(text="◀ Назад к месяцам", callback_data=f"back_month:{date_str}:{svc_id}")])

    kb = types.InlineKeyboardMarkup(inline_keyboard=rows)
    await cb.message.answer(f"Выберите время на {selected_date.strftime('%d.%m.%Y')}", reply_markup=kb)
    await cb.answer()


# При выборе времени -> создаём бронь и уведомляем мастера
@router.callback_query(F.data.startswith("time:"))
async def on_time_selected(cb: types.CallbackQuery):
    # time:YYYY-MM-DD:HH:MM:svc_id
    parts = cb.data.split(":", 3)
    _, date_str, time_str, svc_id = parts
    user_id = cb.from_user.id
    # Создаём бронь в БД
    booking_id = await create_booking(user_id=user_id, service_id=int(svc_id), date_str=date_str, time_str=time_str)
    if not booking_id:
        await cb.message.answer("Ошибка при создании брони. Попробуйте позже.")
        await cb.answer()
        return

    # Отправляем уведомление мастеру с кнопками подтверждения / отклонения
    confirm_kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm:{booking_id}"),
                types.InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject:{booking_id}")
            ]
        ]
    )
    try:
        await cb.bot.send_message(MASTER_ID, f"📩 Новая заявка #{booking_id}\nКлиент: {cb.from_user.full_name}\nУслуга id: {svc_id}\n📅 {date_str}\n⏰ {time_str}", reply_markup=confirm_kb)
    except Exception:
        # если мастер недоступен, всё равно возвращаем пользователю ответ
        pass

    await cb.message.answer("✅ Ваша заявка создана и отправлена мастеру на подтверждение.")
    await cb.answer()
