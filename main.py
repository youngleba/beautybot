import asyncio
import logging
from aiogram import Bot, Dispatcher, executor
from app.database.db import create_db
from app.utils.config_loader import BOT_TOKEN
from app.handlers import register_handlers  # импортируем, но внутри будет register_handlers(dp)

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler("bot.log", mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

async def on_startup(dp):
    try:
        await create_db()
        logging.info("✅ Таблицы из schema.sql успешно созданы или уже существуют.")
    except Exception as e:
        logging.error(f"Ошибка при создании базы данных: {e}")
    register_handlers(dp)
    logging.info("✅ BeautyBot запущен и готов к работе.")

if __name__ == "__main__":
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(bot)
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
