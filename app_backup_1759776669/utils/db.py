# ~/beautybot/app/utils/db.py
import aiosqlite
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parents[1]  # .../app
DB_PATH = BASE_DIR / "database.db"


async def init_db() -> None:
    """
    Создаёт файл БД и необходимые таблицы, а также seed-услуги, если их нет.
    Вызывать один раз при старте (можно вызывать безопасно несколько раз).
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS clients (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                bonus_points INTEGER DEFAULT 0
            );
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price INTEGER DEFAULT 0,
                duration INTEGER DEFAULT 60
            );
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                service_id INTEGER,
                service_name TEXT,
                date TEXT,
                time TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(service_id) REFERENCES services(id)
            );
            """
        )
        await db.commit()

        # seed services если таблица пустая
        async with db.execute("SELECT COUNT(*) FROM services") as cur:
            row = await cur.fetchone()
            count = row[0] if row else 0
        if count == 0:
            await db.executemany(
                "INSERT INTO services (name, price, duration) VALUES (?, ?, ?)",
                [
                    ("Маникюр", 1500, 60),
                    ("Педикюр", 2000, 80),
                    ("Наращивание ресниц", 2500, 90),
                ],
            )
            await db.commit()


# -----------------------
# Функции работы с данными
# -----------------------

async def get_services() -> List[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT id, name, price, duration FROM services ORDER BY id") as cur:
            rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def create_booking(user_id: int, service_id: int, date_str: Optional[str] = None, time_str: Optional[str] = None) -> Optional[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT id, name FROM services WHERE id = ?", (service_id,)) as cur:
            svc = await cur.fetchone()
        if not svc:
            return None
        service_name = svc["name"]
        if date_str is None:
            date_str = datetime.now().date().isoformat()
        if time_str is None:
            time_str = datetime.now().strftime("%H:%M")
        cursor = await db.execute(
            "INSERT INTO bookings (user_id, service_id, service_name, date, time, status) VALUES (?, ?, ?, ?, ?, 'pending')",
            (user_id, service_id, service_name, date_str, time_str),
        )
        await db.commit()
        return cursor.lastrowid


async def get_pending_bookings() -> List[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM bookings WHERE status = 'pending' ORDER BY created_at") as cur:
            rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def update_booking_status(booking_id: int, status: str) -> bool:
    """
    Обновляет статус и возвращает True если статус действительно изменён.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE bookings SET status = ? WHERE id = ?", (status, booking_id))
        await db.commit()
        async with db.execute("SELECT status FROM bookings WHERE id = ?", (booking_id,)) as cur:
            row = await cur.fetchone()
        return bool(row and row[0] == status)


async def get_client_info(booking_id: int) -> Optional[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)) as cur:
            row = await cur.fetchone()
        return dict(row) if row else None


async def add_loyalty_points(user_id: int, points: int) -> int:
    """
    Начисляет баллы пользователю. Возвращает новое количество баллов.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT bonus_points FROM clients WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
        if row:
            new_points = row["bonus_points"] + points
            await db.execute("UPDATE clients SET bonus_points = ? WHERE user_id = ?", (new_points, user_id))
        else:
            new_points = points
            await db.execute("INSERT INTO clients (user_id, bonus_points) VALUES (?, ?)", (user_id, new_points))
        await db.commit()
        return new_points


async def get_client_points(user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT bonus_points FROM clients WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
        return row[0] if row else 0


async def get_user_bookings(user_id: int) -> List[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM bookings WHERE user_id = ? ORDER BY created_at DESC", (user_id,)) as cur:
            rows = await cur.fetchall()
        return [dict(r) for r in rows]

