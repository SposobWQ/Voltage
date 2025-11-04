import os
import ssl
import subprocess
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')

# Проверяем FFmpeg при запуске
try:
    subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    print("✅ FFmpeg доступен")
except (subprocess.CalledProcessError, FileNotFoundError):
    print("❌ FFmpeg не найден!")

# SSL фикс
ssl._create_default_https_context = ssl._create_unverified_context
os.environ['PYTHONHTTPSVERIFY'] = '0'

# Настройки для yt-dlp
YDL_OPTIONS = {
    'format': 'bestaudio[ext=webm]/bestaudio/best',
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
    'extract_flat': False,
    'ssl_verify': False,
    'geo_bypass': True,
    'geo_bypass_country': 'US',
    'socket_timeout': 30,
    'buffersize': 2048,
    'http_chunk_size': 10485760,
}

# Улучшенные настройки звука
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -af "volume=1.0" -bufsize 512k -ac 2 -ar 48000'
}

# ПУТИ ДЛЯ СОХРАНЕНИЯ ДАННЫХ
# На Railway используем /tmp для persistence или внешнее хранилище
IS_RAILWAY = os.getenv('RAILWAY_ENVIRONMENT') is not None

if IS_RAILWAY:
    # На Railway используем том для постоянного хранения
    PLAYLISTS_DIR = "/app/data/playlists"
    # Альтернативно можно использовать /tmp если том не настроен
    if not os.path.exists('/app/data'):
        PLAYLISTS_DIR = "/tmp/music_bot/playlists"
else:
    # Локальная разработка
    PLAYLISTS_DIR = "data/playlists"

# Создаем директорию если не существует
os.makedirs(PLAYLISTS_DIR, exist_ok=True)

# Настройки прав
ADMIN_ROLE_NAMES = ['Admin', 'Administrator', 'Модератор', 'Moderator']
BOT_OWNER_ID = int(os.getenv('BOT_OWNER_ID', '0'))

print(f"✅ Конфигурация загружена")
print(f"📁 Директория плейлистов: {PLAYLISTS_DIR}")
print(f"🚄 Режим Railway: {IS_RAILWAY}")