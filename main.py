import asyncio
from aiogram import Bot, Dispatcher
from app.handlers import register_handlers  # Регистрируем все роутеры
from app.database.db import create_db
from app.utils.config_loader import BOT_TOKEN


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Создаем базу данных (таблицы) при старте
    await create_db()

    # Регистрируем хендлеры
    register_handlers(dp)

    print("✅ BeautyBot запущен и готов к работе.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
