# BeautyBot — Telegram бот для записи клиентов

## 🚀 Быстрый старт

1. Создай `.env` и заполни свои данные:

BOT_TOKEN=твой_токен
MASTER_ID=твой_id
DATABASE_URL=postgresql://user:password@localhost:5432/beautybot


2. Установи зависимости:

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt


3. Запусти:

python main.py


Бот создаёт таблицы автоматически при первом запуске.

✅ Итого — как должно быть на этом этапе
Файл	Состояние
.env	✅ (с твоими реальными данными)
.env.example	⚙️ (по желанию, шаблон)
requirements.txt	✅ (aiogram + dotenv + asyncpg)
.gitignore	✅
README.md	✅ (как выше)
