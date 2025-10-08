# ~/beautybot/app/utils/db.py
"""
Асинхронный модуль работы с SQLite (aiosqlite).
Содержит все функции, которые используются хендлерами:
- init_db
- add_user
- get_services
- create_booking / add_booking
- get_pending_bookings / get_unconfirmed_bookings
- get_booking_by_id / get_client_info
- update_booking_status
- add_loyalty_points
- get_client_points
- get_user_bookings / get_bookings_by_user
"""

from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

import aiosqlite

BASE_DIR = Path(__file__).resolve().parents[1]  # .../app
DB_PATH = BASE_DIR / "database.db"


# -----------------------
# Инициализация БД
# -----------------------
async def init_db() -> None:
    """
    Создаёт таблицы clients, services, bookings и заполняет services seed-услугами, если пусто.
    Безопасно вызывать несколько раз.
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

        # seed services если пусто
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
# Пользователи
# -----------------------
async def add_user(user_id: int, username: Optional[str] = None) -> None:
    """Добавляет пользователя в clients, если его нет; обновляет username если изменился."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM clients WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
        if row:
            if username is not None:
                await db.execute("UPDATE clients SET username = ? WHERE user_id = ?", (username, user_id))
        else:
            await db.execute("INSERT INTO clients (user_id, username, bonus_points) VALUES (?, ?, 0)", (user_id, username))
        await db.commit()


# -----------------------
# Услуги
# -----------------------
async def get_services() -> List[Dict]:
    """Возвращает список сервисов (id, name, price, duration)."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT id, name, price, duration FROM services ORDER BY id") as cur:
            rows = await cur.fetchall()
        return [dict(r) for r in rows]


# -----------------------
# Бронирования
# -----------------------
async def create_booking(user_id: int, service_id: int, date_str: Optional[str] = None, time_str: Optional[str] = None) -> Optional[int]:
    """
    Создаёт запись в bookings и возвращает id новой записи.
    Если service_id не найден — возвращает None.
    """
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

        await db.execute(
            "INSERT INTO bookings (user_id, service_id, service_name, date, time, status) VALUES (?, ?, ?, ?, ?, 'pending')",
            (user_id, service_id, service_name, date_str, time_str),
        )
        await db.commit()

        # Получаем last_insert_rowid() — надёжно в aiosqlite
        async with db.execute("SELECT last_insert_rowid()") as cur2:
            row = await cur2.fetchone()
        return int(row[0]) if row and row[0] is not None else None


# backward-compatible alias (некоторые файлы импортируют add_booking)
add_booking = create_booking


async def get_pending_bookings() -> List[Dict]:
    """Возвращает список записей со статусом 'pending'."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM bookings WHERE status = 'pending' ORDER BY created_at") as cur:
            rows = await cur.fetchall()
        return [dict(r) for r in rows]


# alias для разных вариантов кода
get_unconfirmed_bookings = get_pending_bookings


async def get_booking_by_id(booking_id: int) -> Optional[Dict]:
    """
    Возвращает запись с доп. информацией о цене услуги (если service_id задан).
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT b.*, s.price AS service_price, s.id AS service_id
            FROM bookings b
            LEFT JOIN services s ON b.service_id = s.id
            WHERE b.id = ?
            """, (booking_id,)
        ) as cur:
            row = await cur.fetchone()
        return dict(row) if row else None


# alias
get_client_info = get_booking_by_id


async def update_booking_status(booking_id: int, status: str) -> bool:
    """
    Обновляет статус записи. status — строка ('confirmed', 'approved', 'rejected', 'pending' и т.п.).
    Возвращает True при успешном обновлении.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE bookings SET status = ? WHERE id = ?", (status, booking_id))
        await db.commit()
        return True


# -----------------------
# Бонусы / клиенты
# -----------------------
async def add_loyalty_points(user_id: int, points: int) -> int:
    """
    Начисляет points пользователю, создаёт запись о клиенте при необходимости.
    Возвращает новое количество баллов.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT bonus_points FROM clients WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()

        if row:
            new_points = (row["bonus_points"] or 0) + points
            await db.execute("UPDATE clients SET bonus_points = ? WHERE user_id = ?", (new_points, user_id))
        else:
            new_points = points
            await db.execute("INSERT INTO clients (user_id, username, bonus_points) VALUES (?, ?, ?)", (user_id, None, new_points))

        await db.commit()
        return int(new_points)


async def get_client_points(user_id: int) -> int:
    """Возвращает количество бонусов клиента (0 если нет)."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT bonus_points FROM clients WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
        return int(row[0]) if row and row[0] is not None else 0


# -----------------------
# Просмотр записей пользователя
# -----------------------
async def get_user_bookings(user_id: int) -> List[Dict]:
    """Возвращает все бронирования пользователя (service_name, date, time, status)."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT b.id, b.service_name, b.date, b.time, b.status
            FROM bookings b
            WHERE b.user_id = ?
            ORDER BY b.date DESC, b.time DESC
            """, (user_id,)
        ) as cur:
            rows = await cur.fetchall()
        return [dict(r) for r in rows]


# backward-compatible alias
get_bookings_by_user = get_user_bookings

