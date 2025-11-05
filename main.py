# main.py - Asosiy bot logikasi

import logging
from datetime import datetime
import pytz 

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Importlar
from config import BOT_TOKEN, ADMIN_ID 
from db import init_db, add_chat, get_active_chats, add_scheduled_post, deactivate_chat
from scheduler import check_and_send_posts

# Global sozlamalar
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# APScheduler O'zbekiston vaqt mintaqasida ishlaydi
scheduler = AsyncIOScheduler(timezone="Asia/Tashkent") 

# --- Admin vaziyatlari (FSM) ---
class PostState(StatesGroup):
    waiting_for_post = State()
    waiting_for_schedule_time = State()

# --- ADMIN TEKSHIRUVI ---
def is_admin(user_id: int) -> bool:
    """Faqat ADMIN_ID ro'yxatidagi foydalanuvchilar uchun ruxsat beradi."""
    return user_id in ADMIN_ID

# --- HANDLERS (Buyruqlar va Xabarlar) ---

@dp.message(Command("start"))
async def command_start_handler(message: types.Message):
    if is_admin(message.from_user.id):
        await message.answer(f"Assalomu alaykum, Administrator! 😊\n\nBot ishga tushdi. Faol chatlar soni: **{len(get_active_chats())}**\n\n/newpost - Yangi post rejalashtirish\n/myid - ID raqamingizni olish")
    else:
        await message.answer("Siz administrator emassiz. Bot faqat admin tomonidan boshqariladi.")

@dp.message(Command("myid"))
async def command_myid(message: types.Message):
    await message.answer(f"Sizning ID raqamingiz: `{message.from_user.id}`\n\n*(Uni Render Environment Variables yoki .env ga `ADMIN_ID` sifatida saqlang)*", parse_mode="Markdown")

# --- 1. YANGI POST REJALASHTIRISH ---

@dp.message(Command("newpost"))
async def start_new_post(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return await message.answer("Sizda bu funksiyaga ruxsat yo'q.")
    
    await message.answer("Yubormoqchi bo'lgan postni (matn, rasm, video yoki hujjat) yuboring. Tugmalar qo'shish hozircha qo'llab-quvvatlanmaydi.")
    await state.set_state(PostState.waiting_for_post)

@dp.message(PostState.waiting_for_post, F.content_type.in_({'text', 'photo', 'video', 'document'}))
async def process_post_content(message: types.Message, state: FSMContext):
    media_type = 'text'
    file_id = None
    caption = message.caption or message.text
    
    # Media turini aniqlash va File ID ni olish
    if message.photo:
        media_type = 'photo'
        file_id = message.photo[-1].file_id
    elif message.video:
        media_type = 'video'
        file_id = message.video.file_id
    elif message.document:
        media_type = 'document'
        file_id = message.document.file_id
    elif message.text:
        media_type = 'text'
        # caption allaqachon message.text ga teng

    if not caption and file_id:
        caption = "" # Caption bo'lmasa bo'sh string

    await state.update_data(media_type=media_type, file_id=file_id, caption=caption)
    
    # Kelajakdagi vaqtni kiriting deb foydalanuvchiga aytish uchun
    current_time_uz = datetime.now(pytz.timezone("Asia/Tashkent")).strftime('%Y-%m-%d %H:%M:%S')

    await message.answer(
        f"Post qabul qilindi.\n\nEndi postni qachon yuborish vaqtini kiriting. **Format:** `YYYY-MM-DD HH:MM:SS` (masalan, 2025-11-04 18:30:00)\n\n*(Joriy Toshkent vaqti: {current_time_uz})*"
    )
    await state.set_state(PostState.waiting_for_schedule_time)

@dp.message(PostState.waiting_for_schedule_time)
async def process_schedule_time(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return # Admin tekshiruvi

    try:
        schedule_time_str = message.text.strip()
        schedule_time = datetime.strptime(schedule_time_str, '%Y-%m-%d %H:%M:%S')
        
        # O'tmishdagi vaqtni tekshirish (Endi server vaqtidan foydalanish to'g'ri)
        if schedule_time < datetime.now():
            return await message.answer("Iltimos, kelajakdagi vaqtni kiriting. Vaqt o'tib ketgan.")

        data = await state.get_data()
        
        # DB ga saqlash
        post_id = add_scheduled_post(
            data['media_type'],
            data['file_id'] if data['file_id'] else '',
            data['caption'] if data['caption'] else '',
            schedule_time
        )
        
        await message.answer(
            f"✅ **Post muvaffaqiyatli rejalashtirildi!**\nID: {post_id}\nVaqt: {schedule_time_str}\nManzillar soni: {len(get_active_chats())}"
        , parse_mode="Markdown")
        await state.clear()

    except ValueError:
        await message.answer("Noto'g'ri vaqt formati. Iltimos, `YYYY-MM-DD HH:MM:SS` formatida kiriting.")
    except Exception as e:
        await message.answer(f"Kutilmagan xato: {e}")
        logger.error(f"Rejalashtirishda xato: {e}")
        await state.clear()


# --- 2. XIZMAT XABARLARI (KANALGA QO'SHILISH/O'CHIRILISH) ---

@dp.my_chat_member(F.chat.type.in_({'channel', 'supergroup', 'group'}))
async def bot_added_to_chat(update: types.ChatMemberUpdated):
    """Bot kanal yoki guruhga administrator sifatida qo'shilganda/o'chirilganda ishlaydi."""
    chat_id = update.chat.id
    chat_title = update.chat.title
    
    # Yangi status: 'administrator' yoki 'member' (va post yuborish huquqi)
    new_member = update.new_chat_member
    is_admin_or_member = new_member.status in ['administrator', 'member']
    can_post = getattr(new_member, 'can_post_messages', False) or update.chat.type != 'channel'

    if is_admin_or_member and (can_post or update.chat.type != 'channel'):
        # Chatni faol deb DB ga qo'shish/yangilash
        add_chat(chat_id, chat_title, update.chat.type)
        
        # Adminni ogohlantirish (faqat birinchi admin ID ga yuboriladi)
        if ADMIN_ID and update.old_chat_member.status in ['left', 'kicked', 'restricted']:
            await bot.send_message(
                ADMIN_ID[0], 
                f"✅ **Bot yangi chatga qo'shildi/faollashdi:**\nChat: **{chat_title}**\nID: `{chat_id}`", 
                parse_mode="Markdown"
            )

    # Bot o'chirilganda/bloklanganda
    elif new_member.status in ['left', 'kicked']:
        # Chatni nofaol deb belgilash
        deactivate_chat(chat_id)
        
        # Adminni ogohlantirish
        if ADMIN_ID:
            await bot.send_message(
                ADMIN_ID[0], 
                f"❌ **Bot chatdan chiqarildi/bloklandi:**\nChat: **{chat_title}**\nID: `{chat_id}`. Endi unga postlar yuborilmaydi.",
                parse_mode="Markdown"
            )


# --- BOTNI ISHGA TUSHIRISH FUNKSIYASI (server.py tomonidan chaqiriladi) ---

async def main():
    """Botning asosiy ishga tushirish mantig'i."""
    logger.info("Bot ishga tushirilmoqda...")
    
    # ADMIN_ID ro'yxati bo'sh emasligini tekshirish
    if not BOT_TOKEN or not ADMIN_ID:
        logger.error("BOT_TOKEN yoki ADMIN_ID topilmadi. Bot ishga tushirilmadi.")
        return # Botni ishga tushirishni to'xtatish

    # DB ni ishga tushirish
    try:
        init_db()
    except Exception as e:
        logger.error(f"DB initsializatsiyasida jiddiy xato: {e}. Bot ishga tushirilmadi.")
        return

    # Scheduler ni ishga tushirish (har 1 daqiqada postlarni tekshiradi)
    scheduler.add_job(check_and_send_posts, 'interval', minutes=1, args=(bot,))
    scheduler.start()
    logger.info("Scheduler ishga tushdi.")

    # Botni ishga tushirish (Long Polling)
    await dp.start_polling(bot)

# --- FAYLNING ENG OSTIDAGI QISM BUTUNLAY O'CHIRILDI ---
# (server.py bu main funksiyasini chaqiradi)
