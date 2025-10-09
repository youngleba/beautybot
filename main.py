import asyncio
import logging
from aiogram import Bot, Dispatcher
from app.handlers import register_handlers
from app.database.db import create_db
from app.utils.config_loader import BOT_TOKEN

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='bot.log',
    filemode='a',
)

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    try:
        await create_db()
    except Exception as e:
        logging.error(f"Ошибка при создании базы данных: {e}")

    register_handlers(dp)

    logging.info("✅ BeautyBot запущен и готов к работе.")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Ошибка poll: {e}")

if __name__ == "__main__":
    asyncio.run(main())
