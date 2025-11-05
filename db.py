# db.py - PostgreSQL (psycopg2) ga moslangan yakuniy versiya

import psycopg2
import logging
import pytz 
from datetime import datetime

from config import DATABASE_URL

logger = logging.getLogger(__name__)

# --- BAZA BILAN ALOQA FUNKSIYASI ---
def get_db_connection():
    """PostgreSQL ga ulanishni yaratadi va qaytaradi."""
    if not DATABASE_URL:
        logger.error("DATABASE_URL konfiguratsiyada topilmadi.")
        raise ValueError("DATABASE_URL topilmadi. Iltimos, Render ENV yoki .env da o'rnating.")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        logger.error(f"PostgreSQL ulanishida xato: {e}")
        # Ulanish xatosi bo'lsa, xatoni ko'rsatish
        raise

# --- DEBUG FUNKSIYALARI ---
def debug_check_db_content():
    """Jadvallardagi barcha ma'lumotlarni logga chiqaradi (DEBUG maqsadida)."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Target Chats ma'lumotlarini olish
        cur.execute("SELECT id, title, is_active FROM target_chats;")
        chats = cur.fetchall()
        logger.info(f"DEBUG CHATS: Target Chats ({len(chats)}): {chats}")
        
        # Scheduled Posts ma'lumotlarini olish
        cur.execute("SELECT id, schedule_time, is_sent FROM scheduled_posts;")
        posts = cur.fetchall()
        logger.info(f"DEBUG POSTS: Scheduled Posts ({len(posts)}): {posts}")
        
    except Exception as e:
        logger.error(f"DEBUG XATO: DB tarkibini tekshirishda xato: {e}")
    finally:
        if conn:
            conn.close()

# --- MA'LUMOTLAR BAZASINI INITSIIALIZATSIYA QILISH ---
def init_db():
    """Jadvallar mavjudligini tekshiradi va kerak bo'lsa ularni yaratadi."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 1. target_chats jadvali
        cur.execute("""
            CREATE TABLE IF NOT EXISTS target_chats (
                id BIGINT PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                type VARCHAR(50),
                is_active BOOLEAN DEFAULT TRUE
            );
        """)
        
        # 2. scheduled_posts jadvali
        cur.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_posts (
                id SERIAL PRIMARY KEY,
                media_type VARCHAR(50) NOT NULL,
                file_id TEXT,
                caption TEXT,
                schedule_time TIMESTAMP WITH TIME ZONE NOT NULL,
                is_sent BOOLEAN DEFAULT FALSE
            );
        """)
        
        conn.commit()
        logger.info("PostgreSQL jadvallari muvaffaqiyatli tekshirildi/yaratildi.")
        
        # DB tarkibini tekshirish uchun DEBUG funksiyasini chaqirish
        debug_check_db_content()
        
    except Exception as e:
        logger.error(f"DB initsializatsiyasida xato: {e}")
        raise
    finally:
        if conn:
            conn.close()

# --- CHATLARNI QO'SHISH/YANGILASH ---
def add_chat(chat_id: int, title: str, chat_type: str):
    """Chatni qo'shadi yoki faollashtiradi (agar allaqachon mavjud bo'lsa)."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # INSERT OR UPDATE (UPSERT)
        cur.execute("""
            INSERT INTO target_chats (id, title, type, is_active) 
            VALUES (%s, %s, %s, TRUE)
            ON CONFLICT (id) DO UPDATE 
            SET title = EXCLUDED.title, type = EXCLUDED.type, is_active = TRUE;
        """, (chat_id, title, chat_type))
        conn.commit()
        logger.info(f"Chat {chat_id} muvaffaqiyatli qo'shildi/yangilandi.")
    except Exception as e:
        logger.error(f"Chatni qo'shish/yangilashda xato ({chat_id}): {e}")
    finally:
        if conn:
            conn.close()

# --- BOSHQA DB FUNKSIYALAR ---

def get_active_chats():
    """Barcha faol chat ID'larini qaytaradi."""
    conn = None
    chats = []
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM target_chats WHERE is_active = TRUE;")
        chats = [int(row[0]) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"Faol chatlarni olishda xato: {e}")
    finally:
        if conn:
            conn.close()
    return chats

def add_scheduled_post(media_type: str, file_id: str, caption: str, schedule_time: datetime) -> int:
    """Yangi postni rejalashtirish jadvaliga qo'shadi."""
    conn = None
    post_id = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Vaqtni Toshkent vaqt zonasiga moslash
        tz = pytz.timezone("Asia/Tashkent")
        scheduled_time_tz = tz.localize(schedule_time)
        
        cur.execute("""
            INSERT INTO scheduled_posts (media_type, file_id, caption, schedule_time) 
            VALUES (%s, %s, %s, %s) RETURNING id;
        """, (media_type, file_id, caption, scheduled_time_tz))
        
        post_id = cur.fetchone()[0]
        conn.commit()
    except Exception as e:
        logger.error(f"Postni rejalashtirishda xato: {e}")
    finally:
        if conn:
            conn.close()
    return post_id

def deactivate_chat(chat_id: int):
    """Chatni nofaol deb belgilaydi."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE target_chats SET is_active = FALSE WHERE id = %s;", (chat_id,))
        conn.commit()
    except Exception as e:
        logger.error(f"Chatni nofaol qilishda xato ({chat_id}): {e}")
    finally:
        if conn:
            conn.close()

def get_due_posts():
    """Yuborilishi kerak bo'lgan barcha postlarni qaytaradi."""
    conn = None
    posts = []
    
    # Hozirgi vaqtni Toshkent vaqt zonasida olish
    now = datetime.now(pytz.timezone("Asia/Tashkent")) 
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, media_type, file_id, caption 
            FROM scheduled_posts 
            WHERE is_sent = FALSE AND schedule_time <= %s;
        """, (now,))
        
        for row in cur.fetchall():
            posts.append({
                'id': row[0],
                'media_type': row[1],
                'file_id': row[2],
                'caption': row[3]
            })
            
        if posts:
            logger.info(f"DEBUG: DB dan {len(posts)} ta yuborilishi kerak bo'lgan post topildi.")
            
    except Exception as e:
        logger.error(f"Yuboriladigan postlarni olishda xato: {e}")
    finally:
        if conn:
            conn.close()
    return posts

def mark_post_as_sent(post_id: int):
    """Postni yuborilgan deb belgilaydi."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE scheduled_posts SET is_sent = TRUE WHERE id = %s;", (post_id,))
        conn.commit()
    except Exception as e:
        logger.error(f"Postni yuborilgan deb belgilashda xato ({post_id}): {e}")
    finally:
        if conn:
            conn.close()
