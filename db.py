# db.py fayli

import sqlite3
from datetime import datetime
import os

# config.py dan kerakli sozlamalarni import qilamiz
from config import DB_NAME

def init_db():
    """Ma'lumotlar bazasini va jadvallarni yaratadi."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. Target_Chats jadvali: Bot admin bo'lgan kanallar/guruhlar ro'yxati
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS target_chats (
            chat_id INTEGER PRIMARY KEY,
            chat_title TEXT,
            chat_type TEXT,
            is_active BOOLEAN DEFAULT 1
        )
    """)

    # 2. Scheduled_Posts jadvali: Rejalashtirilgan postlar
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scheduled_posts (
            post_id INTEGER PRIMARY KEY AUTOINCREMENT,
            media_type TEXT,
            file_id TEXT,
            caption TEXT,
            scheduled_time DATETIME,
            is_sent BOOLEAN DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()

# --- TARGET_CHATS FUNKSIYALARI ---

def add_chat(chat_id: int, chat_title: str, chat_type: str):
    """Yangi chatni DB ga qo'shadi yoki faollashtiradi."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO target_chats (chat_id, chat_title, chat_type, is_active)
        VALUES (?, ?, ?, 1)
    """, (chat_id, chat_title, chat_type))
    conn.commit()
    conn.close()

def deactivate_chat(chat_id: int):
    """Chatni nofaol qiladi (bot o'chirilganda)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE target_chats SET is_active = 0 WHERE chat_id = ?
    """, (chat_id,))
    conn.commit()
    conn.close()

def get_active_chats():
    """Faol chat ID'lari ro'yxatini qaytaradi."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM target_chats WHERE is_active = 1")
    chats = [row[0] for row in cursor.fetchall()]
    conn.close()
    return chats

# --- SCHEDULED_POSTS FUNKSIYALARI ---

def add_scheduled_post(media_type: str, file_id: str, caption: str, schedule_time: datetime):
    """Rejalashtirilgan postni DB ga saqlaydi."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO scheduled_posts (media_type, file_id, caption, scheduled_time)
        VALUES (?, ?, ?, ?)
    """, (media_type, file_id, caption, schedule_time.strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    post_id = cursor.lastrowid
    conn.close()
    return post_id

def get_due_posts():
    """Yuborish vaqti kelgan postlarni (yuborilmagan) qaytaradi."""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT post_id, media_type, file_id, caption
        FROM scheduled_posts
        WHERE is_sent = 0 AND scheduled_time <= ?
    """, (now,))
    posts = cursor.fetchall()
    conn.close()
    return posts

def mark_post_as_sent(post_id: int):
    """Postni 'yuborilgan' deb belgilaydi."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE scheduled_posts SET is_sent = 1 WHERE post_id = ?
    """, (post_id,))
    conn.commit()
    conn.close()
