import os
import logging
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MASTER_ID = os.getenv("MASTER_ID")
DATABASE_URL = os.getenv("DATABASE_URL")

if BOT_TOKEN is None:
    logging.error("Ошибка: переменная окружения BOT_TOKEN не установлена!")

if MASTER_ID is None:
    logging.error("Ошибка: переменная окружения MASTER_ID не установлена!")
else:
    try:
        MASTER_ID = int(MASTER_ID)
    except ValueError:
        logging.error("Ошибка: переменная MASTER_ID должна быть числом!")
        MASTER_ID = None

if DATABASE_URL is None:
    logging.error("Ошибка: переменная окружения DATABASE_URL не установлена!")
