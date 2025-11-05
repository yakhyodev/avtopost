# server.py fayli (Render Web Service uchun yechim)

import os
import asyncio
from main import main as bot_main 
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import logging

logger = logging.getLogger(__name__)

# Render atrof-muhit o'zgaruvchisidan PORT ni oladi
PORT = int(os.environ.get('PORT', 8080))

class HealthCheckHandler(BaseHTTPRequestHandler):
    """Renderning "ochiq port" talabini qondirish uchun oddiy HTTP server."""
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Bot is running.')

def start_health_check_server():
    """HTTP serverni alohida threadda ishga tushiradi."""
    server_address = ('0.0.0.0', PORT)
    httpd = HTTPServer(server_address, HealthCheckHandler)
    logger.info(f"Health Check Server {PORT} portida ishga tushdi.")
    httpd.serve_forever()

async def run_bot_and_server():
    """Botni va HTTP serverni birga ishga tushiradi."""
    
    # 1. HTTP serverni alohida jarayon/thread da ishga tushirish
    server_thread = threading.Thread(target=start_health_check_server)
    server_thread.daemon = True # Asosiy dastur to'xtasa, bu ham to'xtasin
    server_thread.start()

    # 2. Asosiy bot funksiyasini ishga tushirish (Long Polling)
    await bot_main() 
    
if __name__ == "__main__":
    try:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        logger.info(f"Server {PORT} portida va Bot ishga tushirilmoqda...")
        asyncio.run(run_bot_and_server())
    except Exception as e:
        logger.error(f"Asosiy ishga tushirish xatosi: {e}")
