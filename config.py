# config.py fayli

import os
from dotenv import load_dotenv

# Lokal ishga tushirish uchun .env ni yuklaymiz
load_dotenv()

# --- BOT UCHUN ASOSIY KONFIGURATSIYA ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_NAME = "bot_data.db"

# --- ADMIN IDS UCHUN YETCHIM ---
# .env dan ADMIN_ID qiymatini string sifatida o'qish (masalan: "12345,98765")
admin_id_str = os.getenv("ADMIN_ID") 

# Stringni qayta ishlash va List[int] ga aylantirish
if admin_id_str:
    # Stringni vergul bo'yicha ajratish va har bir elementni intga aylantirish
    ADMIN_ID = [int(id.strip()) for id in admin_id_str.split(',')]
else:
    # Agar ID topilmasa, bo'sh ro'yxat qaytariladi
    ADMIN_ID = []
