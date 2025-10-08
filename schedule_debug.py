import asyncio
import sys
from datetime import date

sys.path.append("app")  # добавляем папку app в путь
from database.schedule import get_master_schedule  # импортируем правильно

async def main():
    slots = await get_master_schedule(date.today(), 1)
    print("Слоты:", slots)

asyncio.run(main())
