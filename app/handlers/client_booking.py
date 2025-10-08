from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime, timedelta
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.utils.db import get_services, get_service_by_id, save_booking_to_db  # <── исправлено!

router = Router()


class BookingState(StatesGroup):
    choosing_service = State()
    choosing_date = State()
    choosing_time = State()
    confirming = State()


@router.message(F.text == "Записаться")
async def start_booking(message: types.Message, state: FSMContext):
    services = await get_services()
    kb = InlineKeyboardBuilder()
    for s in services:
        kb.button(text=s["name"], callback_data=f"service_{s['id']}")
    kb.adjust(1)
    await message.answer("Выберите услугу:", reply_markup=kb.as_markup())
    await state.set_state(BookingState.choosing_service)


@router.callback_query(F.data.startswith("service_"))
async def choose_service(callback: types.CallbackQuery, state: FSMContext):
    service_id = int(callback.data.split("_")[1])
    await state.update_data(service_id=service_id)

    kb = InlineKeyboardBuilder()
    today = datetime.now().date()
    for i in range(5):
        day = today + timedelta(days=i)
        kb.button(text=day.strftime("%d.%m"), callback_data=f"date_{day}")
    kb.adjust(3)
    await callback.message.edit_text("Выберите дату:", reply_markup=kb.as_markup())
    await state.set_state(BookingState.choosing_date)


@router.callback_query(F.data.startswith("date_"))
async def choose_date(callback: types.CallbackQuery, state: FSMContext):
    date_str = callback.data.split("_")[1]
    await state.update_data(date=date_str)

    times = ["10:00", "12:00", "14:00", "16:00", "18:00"]
    kb = InlineKeyboardBuilder()
    for t in times:
        kb.button(text=t, callback_data=f"time_{t}")
    kb.adjust(3)
    await callback.message.edit_text("Выберите время:", reply_markup=kb.as_markup())
    await state.set_state(BookingState.choosing_time)


@router.callback_query(F.data.startswith("time_"))
async def confirm_booking(callback: types.CallbackQuery, state: FSMContext):
    time_str = callback.data.split("_")[1]
    data = await state.get_data()
    service = await get_service_by_id(data["service_id"])

    await state.update_data(time=time_str)

    text = (
        f"📅 <b>Подтверждение записи:</b>\n\n"
        f"Услуга: {service['name']}\n"
        f"Дата: {data['date']}\n"
        f"Время: {time_str}\n\n"
        "Подтвердить запись?"
    )

    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Подтвердить", callback_data="confirm_yes")
    kb.button(text="❌ Отменить", callback_data="confirm_no")
    kb.adjust(2)

    await callback.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")
    await state.set_state(BookingState.confirming)


@router.callback_query(F.data == "confirm_yes")
async def save_booking(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await save_booking_to_db(callback.from_user.id, data["service_id"], data["date"], data["time"])
    await callback.message.edit_text("✅ Запись успешно создана! Ожидайте подтверждения мастера.")
    await state.clear()


@router.callback_query(F.data == "confirm_no")
async def cancel_booking(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("❌ Запись отменена.")
    await state.clear()

