import aiosqlite

DB_PATH = "app/database.db"


async def init_db():
    """Создаёт таблицы, если их ещё нет"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                duration INTEGER NOT NULL,
                price REAL NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER,
                service_id INTEGER,
                date TEXT,
                time TEXT,
                status TEXT DEFAULT 'pending'
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                points INTEGER DEFAULT 0,
                name TEXT
            )
        """)
        await db.commit()


# ======== БЛОК С УСЛУГАМИ ========

async def get_services():
    """Возвращает список всех услуг"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id, name, duration, price FROM services")
        rows = await cursor.fetchall()
        await cursor.close()
        return rows


async def get_service_by_id(service_id: int):
    """Возвращает услугу по ID"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, name, duration, price FROM services WHERE id = ?",
            (service_id,),
        )
        row = await cursor.fetchone()
        await cursor.close()
        return row


# ======== БЛОК С БРОНИРОВАНИЕМ ========

async def save_booking_to_db(client_id: int, service_id: int, date: str, time: str):
    """Сохраняет новую бронь"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO bookings (client_id, service_id, date, time, status) VALUES (?, ?, ?, ?, ?)",
            (client_id, service_id, date, time, "pending"),
        )
        await db.commit()


async def get_booking_by_id(booking_id: int):
    """Получает бронь по ID"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, client_id, service_id, date, time, status FROM bookings WHERE id = ?",
            (booking_id,),
        )
        row = await cursor.fetchone()
        await cursor.close()
        return row


async def get_pending_bookings():
    """Возвращает все ожидающие подтверждения брони"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT id, client_id, service_id, date, time, status
            FROM bookings
            WHERE status = 'pending'
            ORDER BY date, time
        """)
        rows = await cursor.fetchall()
        await cursor.close()
        return rows


async def update_booking_status(booking_id: int, status: str):
    """Обновляет статус брони (approved / rejected / completed)"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE bookings SET status = ? WHERE id = ?",
            (status, booking_id),
        )
        await db.commit()


# ======== БЛОК С КЛИЕНТАМИ И БАЛЛАМИ ========

async def get_client_points(telegram_id: int) -> int:
    """Возвращает количество баллов клиента"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT points FROM clients WHERE telegram_id = ?",
            (telegram_id,),
        )
        row = await cursor.fetchone()
        await cursor.close()
        return row[0] if row else 0


async def add_client_points(telegram_id: int, points: int):
    """Добавляет баллы клиенту"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO clients (telegram_id, points)
            VALUES (?, ?)
            ON CONFLICT(telegram_id)
            DO UPDATE SET points = points + excluded.points
        """, (telegram_id, points))
        await db.commit()


async def get_client_info(telegram_id: int):
    """Возвращает информацию о клиенте"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, telegram_id, points, name FROM clients WHERE telegram_id = ?",
            (telegram_id,),
        )
        row = await cursor.fetchone()
        await cursor.close()
        return row

