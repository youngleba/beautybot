import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MASTER_ID = int(os.getenv("MASTER_ID"))  # Приводим к int, так как это числовой telegram ID
DATABASE_URL = os.getenv("DATABASE_URL")
