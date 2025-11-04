import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')

# Настройки для yt-dlp с отключенной SSL проверкой
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': False,
    'nocheckcertificate': True,  # Важно: отключаем проверку сертификата
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'extract_flat': False,
    'geo_bypass': True,
    'geo_bypass_country': 'US',
    'ssl_verify': False,  # Отключаем SSL verification
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

# Пути
PLAYLISTS_DIR = "data/playlists"
os.makedirs(PLAYLISTS_DIR, exist_ok=True)

print("✅ Конфигурация загружена")