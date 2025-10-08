# ~/beautybot/app/handlers/start.py
from aiogram import Router, types
from aiogram.filters import Command
from app.utils.db import get_client_points

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    """
    Отправляется при запуске бота пользователем.
    """
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name

    points = await get_client_points(user_id)
    text = (
        f"👋 Привет, <b>{username}</b>!\n\n"
        "Я помогу тебе записаться на услуги 💅\n"
        "Можно выбрать услугу, время и ждать подтверждения от мастера.\n\n"
        f"💎 Твои бонусы: <b>{points}</b> баллов"
    )

    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [types.KeyboardButton(text="📅 Записаться")],
            [types.KeyboardButton(text="💎 Мои бонусы")],
        ],
    )

    await message.answer(text, reply_markup=keyboard)

