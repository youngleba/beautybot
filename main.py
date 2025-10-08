from aiogram import Bot, Dispatcher, executor
from dotenv import load_dotenv
import os
from app.handlers import register_handlers

load_dotenv()
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher(bot)

register_handlers(dp)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
