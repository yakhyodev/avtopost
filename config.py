# config.py fayli

import os
from dotenv import load_dotenv

# Faqat lokal ishga tushirish uchun .env ni yuklaymiz. Renderda bu shart emas.
load_dotenv()

# --- BOT UCHUN ASOSIY KONFIGURATSIYA ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_NAME = "bot_data.db"

# --- ADMIN IDS UCHUN YETCHIM ---
# .env dan ADMIN_ID qiymatini string sifatida o'qish (masalan: "12345,98765")
admin_id_str = os.getenv("ADMIN_ID") 

# Stringni qayta ishlash va List[int] ga aylantirish
if admin_id_str:
    # 1. Vergul bo'yicha ajratish
    # 2. Har bir ID ning bosh va oxiridagi bo'shliqlarni olib tashlash (strip())
    # 3. Uni butun songa (int) aylantirish
    ADMIN_ID = [int(id.strip()) for id in admin_id_str.split(',')]
else:
    # Agar hech qanday ID kiritilmasa (yoki .env da topilmasa), bo'sh ro'yxat qaytariladi
    ADMIN_ID = [] 

# ADMIN_ID endi barcha admin ID raqamlarini o'z ichiga olgan Python List'i [12345, 98765]
