from aiogram import types
from aiogram.dispatcher import Dispatcher

def register_handlers(dp: Dispatcher):
    @dp.message_handler(commands=['start'])
    async def start(msg: types.Message):
        await msg.answer("Привет! 👋 Это BeautyBot. Запишись на услугу!")
