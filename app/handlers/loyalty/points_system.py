from aiogram import Router, types
from aiogram.filters import Command
from app.utils.config_loader import DATABASE_URL, MASTER_ID
import asyncpg

router = Router()

BONUS_PERCENT = 5  # % от стоимости услуги
SERVICE_PRICES = {
    "Маникюр": 1500,
    "Стрижка": 2000,
    "Массаж": 2500
}

# === 1. Начисление бонусов после подтверждения ===
async def add_loyalty_points(client_id: int, service: str):
    price = SERVICE_PRICES.get(service, 0)
    points = int(price * BONUS_PERCENT / 100)
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute("""
            INSERT INTO loyalty (client_id, points)
            VALUES ($1, $2)
            ON CONFLICT (client_id)
            DO UPDATE SET points = loyalty.points + EXCLUDED.points
        """, client_id, points)
    finally:
        await conn.close()
    return points

# === 2. Команда /points — показать баланс ===
@router.message(Command("points"))
async def show_points(message: types.Message):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        result = await conn.fetchrow("SELECT points FROM loyalty WHERE client_id=$1", message.from_user.id)
        points = result["points"] if result else 0
    finally:
        await conn.close()
    await message.answer(f"💰 У вас {points} бонусных баллов!")

# === 3. Команда /clients — список клиентов (для мастера) ===
@router.message(Command("clients"))
async def show_clients(message: types.Message):
    if message.from_user.id != MASTER_ID:
        await message.answer("⛔ Доступ запрещён")
        return
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        rows = await conn.fetch("""
            SELECT DISTINCT a.client_id, c.username, c.full_name
            FROM appointments a
            LEFT JOIN clients c ON c.id = a.client_id
        """)
    finally:
        await conn.close()

    if not rows:
        await message.answer("Пока нет клиентов 😔")
        return

    text = "📋 Клиенты:\n"
    for row in rows:
        name = row["full_name"] or row["username"]
        text += f"• {name} (ID: {row['client_id']})\n"

    await message.answer(text)

# === 4. Команда /stats — статистика доходов ===
@router.message(Command("stats"))
async def show_stats(message: types.Message):
    if message.from_user.id != MASTER_ID:
        await message.answer("⛔ Доступ запрещён")
        return
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        rows = await conn.fetch("""
            SELECT service, COUNT(*) AS count
            FROM appointments
            WHERE status='approved'
            GROUP BY service
        """)
    finally:
        await conn.close()

    if not rows:
        await message.answer("Нет данных для статистики.")
        return

    total_income = 0
    text = "📊 Статистика по услугам:\n"
    for row in rows:
        service, count = row["service"], row["count"]
        income = SERVICE_PRICES.get(service, 0) * count
        total_income += income
        text += f"• {service}: {count} записей = {income}₽\n"

    text += f"\n💵 Общий доход: {total_income}₽"
    await message.answer(text)
