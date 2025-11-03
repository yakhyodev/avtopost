# scheduler.py fayli

from datetime import datetime
import asyncio
import logging
import pytz # pytz APScheduler uchun vaqt mintaqalarini boshqarish uchun kerak

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

import db

# Logging sozlamasi
logger = logging.getLogger(__name__)

async def check_and_send_posts(bot: Bot):
    """Vaqti kelgan postlarni tekshiradi va barcha faol chatlarga yuboradi."""
    posts = db.get_due_posts()
    active_chats = db.get_active_chats()

    if not posts:
        return

    # Har bir yuborilishi kerak bo'lgan post uchun
    for post_id, media_type, file_id, caption in posts:
        
        # Har bir faol chatga yuborish
        for chat_id in active_chats:
            try:
                # Post turiga qarab tegishli metodni chaqirish
                if media_type == 'text':
                    await bot.send_message(chat_id, caption)
                elif media_type == 'photo':
                    await bot.send_photo(chat_id, photo=file_id, caption=caption)
                elif media_type == 'video':
                    await bot.send_video(chat_id, video=file_id, caption=caption)
                elif media_type == 'document':
                    await bot.send_document(chat_id, document=file_id, caption=caption)
                
                await asyncio.sleep(0.5)  # Telegram API limitlariga tushmaslik uchun kutish

            except TelegramAPIError as e:
                # Chat admin tekshiruvida yoki yuborishda xato
                error_message = str(e)
                if 'chat not found' in error_message or 'bot is not a member' in error_message or 'not an administrator' in error_message:
                    # Agar bot chatdan o'chirilgan bo'lsa, uni nofaol deb belgilash
                    logger.warning(f"Chat {chat_id} ({db.get_chat_title(chat_id) if hasattr(db, 'get_chat_title') else 'Noma\'lum'}) da xato: {error_message}. Nofaol qilinadi.")
                    db.deactivate_chat(chat_id)
                else:
                    logger.error(f"Post {post_id} ni chat {chat_id} ga yuborishda kutilmagan xato: {error_message}")
            except Exception as e:
                logger.error(f"Noma'lum xato yuz berdi: {e}")

        # Barcha chatlarga yuborilgandan so'ng, postni yuborilgan deb belgilash
        db.mark_post_as_sent(post_id)
        logger.info(f"Post ID {post_id} muvaffaqiyatli yuborildi va belgilandi.")
