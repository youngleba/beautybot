from aiogram import Router, types
from aiogram.filters import Command

router = Router()

@router.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("👋 Привет! Это BeautyBot. Запишись на услугу или напиши /panel, если ты мастер.")
