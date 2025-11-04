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
    'buffersize': 1024,
    'http_chunk_size': 10485760,
}

# Улучшенные настройки FFmpeg для качества
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -analyzeduration 0 -probesize 32M -fflags +genpts',
    'options': '-vn -af "volume=0.8, highpass=f=200, lowpass=f=3000, aresample=48000" -bufsize 512k -ac 2 -ar 48000'
}

PLAYLISTS_DIR = "/app/data/playlists"
os.makedirs(PLAYLISTS_DIR, exist_ok=True)

# Настройки прав
ADMIN_ROLE_NAMES = ['Admin', 'Administrator', 'Модератор', 'Moderator']
BOT_OWNER_ID = int(os.getenv('BOT_OWNER_ID', '0'))

print("✅ Конфигурация загружена")