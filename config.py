# config.py fayli

import os
from dotenv import load_dotenv

# Lokal ishga tushirish uchun .env ni yuklaymiz
load_dotenv()

# --- BOT UCHUN ASOSIY KONFIGURATSIYA ---
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Tashqi DB uchun yangi o'zgaruvchi. Render yoki .env dan o'qiladi.
# Bu qiymat sizning Neon.tech dan olgan manzil (postgresql://...) bo'ladi.
DATABASE_URL = os.getenv("DATABASE_URL") 

# DB_NAME endi kerak emas, lekin boshqa joyda ishlatilgan bo'lsa qoldirish mumkin.
# Agar ishlatilmasa, olib tashlashingiz mumkin. Hozircha qoldiramiz.
DB_NAME = "bot_data.db" 

# --- ADMIN IDS UCHUN YETCHIM ---
# .env dan ADMIN_ID qiymatini string sifatida o'qish 
admin_id_str = os.getenv("ADMIN_ID") 

# Stringni qayta ishlash va List[int] ga aylantirish
if admin_id_str:
    # Qo'shimcha xavfsizlik uchun trim qilingan ID larni int ga aylantirish
    ADMIN_ID = [int(id.strip()) for id in admin_id_str.split(',')]
else:
    # Agar ID topilmasa, bo'sh ro'yxat qaytariladi
    ADMIN_ID = []
