from aiogram import Router, types
from aiogram.filters import Command
from app.utils.db import get_client_points

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    pts = await get_client_points(message.from_user.id)
    kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="📅 Записаться")],
            [types.KeyboardButton(text="🧾 Мои записи"), types.KeyboardButton(text="💎 Бонусы")]
        ],
        resize_keyboard=True
    )
    await message.answer(f"👋 Привет, {message.from_user.first_name}!\n\n💎 У тебя {pts} бонусных баллов.", reply_markup=kb)
