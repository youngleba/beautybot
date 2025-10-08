import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

async def create_db():
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT UNIQUE,
            name TEXT,
            phone TEXT,
            points INTEGER DEFAULT 0
        );
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id SERIAL PRIMARY KEY,
            client_id BIGINT REFERENCES clients(telegram_id),
            service TEXT,
            datetime TIMESTAMP,
            status TEXT DEFAULT 'pending'
        );
    """)
    await conn.close()
    print("✅ Database ready!")
