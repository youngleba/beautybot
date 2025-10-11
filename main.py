import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from app.database.db import create_db
from app.utils.config_loader import BOT_TOKEN

from app.handlers.client.booking import router as booking_router  # For 3.x Router
from app.handlers.master.panel import router as panel_router

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler("bot.log", mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

async def on_startup():
    await create_db()
    logging.info("✅ DB ready")

async def main():
    storage = MemoryStorage()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=storage)
    dp.include_router(booking_router)
    dp.include_router(panel_router)
    await on_startup()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
