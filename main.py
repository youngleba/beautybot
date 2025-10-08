import asyncio
import logging
import sys
import os

# Убедимся, что app в пути
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from app.handlers import start, client_booking, master_panel
from app.utils.db import init_db
from app.keyboards.main_kb import get_main_kb  # исправлено

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN") or "твой_токен_бота"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

main_kb = get_main_kb()  # добавлено

async def set_commands():
    commands = [
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="master", description="Панель мастера"),
    ]
    await bot.set_my_commands(commands)


async def main():
    logger.info("✅ Инициализация БД...")
    await init_db()
    logger.info("✅ Инициализация БД завершена")

    dp.include_router(start.router)
    dp.include_router(client_booking.router)
    dp.include_router(master_panel.router)

    await set_commands()
    logger.info("🤖 Бот запущен и готов к работе")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

