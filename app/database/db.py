import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

async def create_db():
    conn = await asyncpg.connect(DATABASE_URL)
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    if os.path.exists(schema_path):
        with open(schema_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        await conn.execute(sql_script)
        print("✅ Таблицы из schema.sql успешно созданы или уже существуют.")
    else:
        print("⚠️ Файл schema.sql не найден!")
    await conn.close()
