# scheduler.py fayli (Tuzatilgan versiya)

import asyncio
import logging
from datetime import datetime
import pytz 

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

import db # db.py faylini import qilish

# Logging sozlamasi
logger = logging.getLogger(__name__)

async def check_and_send_posts(bot: Bot):
    """Vaqti kelgan postlarni tekshiradi va barcha faol chatlarga yuboradi."""
    
    # 1. Bazadan yuborilishi kerak bo'lgan postlarni olish
    posts = db.get_due_posts() # Natija: Lug'atlar ro'yxati (List of dicts)
    
    # Post topilmasa funksiyadan chiqish
    if not posts:
        return

    # 2. Barcha faol chat ID'larini olish
    active_chats = db.get_active_chats()

    # Har bir yuborilishi kerak bo'lgan post uchun
    # Bu yerda post lug'at (dict) sifatida qabul qilinadi
    for post in posts:
        # Lug'atdan ma'lumotlarni o'qish
        post_id = post['id'] 
        media_type = post['media_type']
        file_id = post['file_id']
        caption = post['caption']

        # Yuborish harakati muvaffaqiyatli bo'lganini kuzatish uchun bayroq
        # Agar bitta chatga ham yuborilsa true bo'ladi
        send_successful = False
        
        # Har bir faol chatga yuborish
        for chat_id in active_chats:
            try:
                # Post turiga qarab tegishli metodni chaqirish
                if media_type == 'text':
                    await bot.send_message(chat_id, caption)
                elif media_type == 'photo':
                    # media_type ga mos ravishda parametr nomini berish
                    await bot.send_photo(chat_id, photo=file_id, caption=caption) 
                elif media_type == 'video':
                    await bot.send_video(chat_id, video=file_id, caption=caption)
                elif media_type == 'document':
                    await bot.send_document(chat_id, document=file_id, caption=caption)
                
                # Agar yuborish muvaffaqiyatli bo'lsa
                send_successful = True
                await asyncio.sleep(0.5) # Telegram API limitlariga tushmaslik uchun kutish

            except TelegramAPIError as e:
                # Xatolikni qayd qilish
                error_message = str(e)
                logger.error(f"Post {post_id} ni chat {chat_id} ga yuborishda xato: {error_message}")
                
                # Chat admin tekshiruvida yoki yuborishda xato bo'lsa
                if 'chat not found' in error_message or 'bot is not a member' in error_message or 'not an administrator' in error_message:
                    # Agar bot chatdan o'chirilgan bo'lsa, uni nofaol deb belgilash
                    logger.warning(f"Chat {chat_id} da post yuborish xatosi. Chat nofaol qilinadi.")
                    db.deactivate_chat(chat_id)
                continue # Keyingi chatga o'tish
                
            except Exception as e:
                logger.error(f"Post {post_id} ni yuborishda kutilmagan xato: {e}")
                continue # Keyingi chatga o'tish

        # 4. Agar kamida bitta chatga ham yuborish muvaffaqiyatli bo'lsa, postni yuborilgan deb belgilash
        if send_successful:
            db.mark_post_as_sent(post_id) 
            logger.info(f"Post ID {post_id} muvaffaqiyatli yuborildi va belgilandi.")
        else:
            logger.warning(f"Post ID {post_id} hech qaysi chatga yuborilmadi. Yuborilgan deb belgilanmadi.")

# Funksiyani to'g'ri chaqirish uchun
# if __name__ == "__main__":
#     # Faqat lokal sinov uchun
#     pass
