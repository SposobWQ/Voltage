import os
import ssl
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')

# ФИКС SSL ОШИБКИ - добавляем в самое начало
ssl._create_default_https_context = ssl._create_unverified_context
os.environ['PYTHONHTTPSVERIFY'] = '0'

# Настройки для yt-dlp с SSL фиксом
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': False,
    'nocheckcertificate': True,  # КРИТИЧЕСКИ ВАЖНО
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'extract_flat': False,
    'ssl_verify': False,  # Явно отключаем SSL проверку
    'geo_bypass': True,
    'geo_bypass_country': 'US',
    'socket_timeout': 30,
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

# Пути
PLAYLISTS_DIR = "data/playlists"
os.makedirs(PLAYLISTS_DIR, exist_ok=True)

print("✅ Конфигурация загружена с SSL фиксом")