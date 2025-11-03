# config.py fayli

import os
from dotenv import load_dotenv

# Faqat lokal ishga tushirish uchun .env ni yuklaymiz. Renderda bu shart emas.
load_dotenv()

# Konfiguratsiyalar (Render Environment Variables dan olinadi)
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
DB_NAME = "bot_data.db"
