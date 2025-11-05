# server.py - Render uchun Health Check serveri va Bot Polling boshqaruvchisi

import os
import threading
import asyncio
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
import signal # Serverni SIGTERM signali orqali to'xtatish uchun

# Logging sozlamalari (main.py dan mustaqil ishlashi uchun)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Render Environment Variable'dan PORT ni olish
# Agar o'rnatilmagan bo'lsa, standart 8080 ishlatiladi
PORT = int(os.environ.get("PORT", 8080))

# Bot Polling jarayonini saqlash uchun global o'zgaruvchi
polling_task = None

# --- HTTP HANDLER (501 NOT IMPLEMENTED XATOSINI TUZATISH) ---

class HealthCheckHandler(BaseHTTPRequestHandler):
    """
    Render'dan kelgan Health Check so'rovlariga javob berish uchun klass.
    501 xatosini oldini olish uchun asosiy HTTP metodlarga javob beradi.
    """
    
    def _send_response(self):
        """Javob yuborish uchun yordamchi funksiya."""
        self.send_response(200) # 200 OK
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Bot is running and awake.")

    def do_GET(self):
        """GET so'roviga javob beradi (Standart Health Check)."""
        self._send_response()

    def do_HEAD(self):
        """HEAD so'roviga javob beradi."""
        self._send_response()
        
    def do_POST(self):
        """POST so'roviga javob beradi (Agar ping POST bo'lsa)."""
        self._send_response()
        
    def log_message(self, format, *args):
        """HTTP serverning keraksiz loglarini o'chiradi."""
        return 

# --- SERVER BOSHQARUVI ---

httpd = None # Global HTTP server obyekti

def start_health_check_server():
    """
    HTTP serverni alohida thread'da ishga tushiradi. 
    Bu Renderga botning tezda javob berishini ta'minlaydi.
    """
    global httpd
    server_address = ('0.0.0.0', PORT)
    try:
        httpd = HTTPServer(server_address, HealthCheckHandler)
        logger.info(f"Health Check Server 0.0.0.0:{PORT} portida ishga tushdi.")
        httpd.serve_forever()
    except Exception as e:
        logger.error(f"HTTP Serverni ishga tushirishda xato: {e}")

def stop_health_check_server(signum=None, frame=None):
    """SIGTERM signali kelganda serverni to'xtatadi."""
    global httpd, polling_task
    logger.warning("SIGTERM signali qabul qilindi. Serverni to'xtatish...")
    
    if httpd:
        # HTTP serverni to'xtatish
        threading.Thread(target=httpd.shutdown).start()
        
    if polling_task:
        # Bot Pollingni bekor qilish
        polling_task.cancel()
        logger.info("Bot Polling bekor qilindi.")

# --- ASOSIY JARAYONLARNI BIRGA BOSHQARISH ---

async def run_bot_and_server(main_func):
    """
    Bot Pollingni va HTTP Health Check serverni birga boshqaradi.
    """
    global polling_task
    
    # SIGTERM (Render tomonidan to'xtatish buyrug'i) handlerini o'rnatish
    signal.signal(signal.SIGTERM, stop_health_check_server)

    # 1. HTTP serverni alohida thread'da ishga tushirish (Renderga tez javob berish uchun)
    server_thread = threading.Thread(target=start_health_check_server)
    server_thread.daemon = True 
    server_thread.start()
    
    # 2. HTTP server ishga tushishini kutish (Kerakli, ammo main.py ning boshqaruviga beriladi)
    await asyncio.sleep(2) 
    
    # 3. HTTP server ishga tushgach, asosiy bot funksiyasini ishga tushirish
    logger.info("Telegram Polling boshlanmoqda...")
    polling_task = asyncio.create_task(main_func()) # main.py dagi main() funksiyasi
    
    try:
        await polling_task
    except asyncio.CancelledError:
        logger.info("Bot Polling jarayoni bekor qilindi.")
    except Exception as e:
        logger.error(f"Bot Polling jarayonida kutilmagan xato: {e}")
        stop_health_check_server()


if __name__ == "__main__":
    # main.py dagi asosiy asyncio.run(main()) o'rniga, bu faylni ishga tushiramiz
    try:
        # main.py dan main funksiyasini import qilish talab qilinadi!
        from main import main as bot_main
        
        asyncio.run(run_bot_and_server(bot_main))
        
    except ImportError:
        logger.error("Xato: main.py faylidan main funksiyasi import qilinmadi. Tekshiring!")
    except Exception as e:
        logger.error(f"Asosiy server xatosi: {e}")
