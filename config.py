import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')

# Проверяем, запущены ли на Railway
IS_RAILWAY = os.getenv('RAILWAY_ENVIRONMENT') is not None

# Настройки для yt-dlp
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': False,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

# Пути
PLAYLISTS_DIR = "data/playlists"
os.makedirs(PLAYLISTS_DIR, exist_ok=True)

print(f"🚄 Режим: {'Railway' if IS_RAILWAY else 'Локальный'}")