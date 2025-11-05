import os
import ssl
import random
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

print("⚙️ Загрузка конфигурации...")

BOT_TOKEN = os.getenv('BOT_TOKEN')

if not BOT_TOKEN:
    print("❌ BOT_TOKEN не найден!")
else:
    print("✅ BOT_TOKEN загружен")

# SSL фикс
ssl._create_default_https_context = ssl._create_unverified_context
os.environ['PYTHONHTTPSVERIFY'] = '0'
print("🔒 SSL фикс активирован")

# Проверяем куки файл
COOKIES_LOADED = False
COOKIES_FILE = 'cookies.txt'

if os.path.exists(COOKIES_FILE):
    file_size = os.path.getsize(COOKIES_FILE)
    print(f"✅ Файл куки найден: {COOKIES_FILE} ({file_size} байт)")
    COOKIES_LOADED = True
else:
    print("⚠️ Файл куки не найден")

# НАСТРОЙКИ YT-DLP
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'socket_timeout': 30,
    'extract_flat': False,
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    },
}

# Добавляем куки если они загружены
if COOKIES_LOADED:
    YDL_OPTIONS['cookiefile'] = COOKIES_FILE
    print("🎯 Куки активированы - возрастные ограничения будут обходиться")
else:
    print("⚠️ Куки не активированы")

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -af "volume=0.5"'
}

# Настройки путей
if os.getenv('RAILWAY_ENVIRONMENT'):
    PLAYLISTS_DIR = "/app/data/playlists"
    print("🚄 Режим Railway: используем persistent storage")
else:
    PLAYLISTS_DIR = "./data/playlists"
    print("💻 Локальный режим")

os.makedirs(PLAYLISTS_DIR, exist_ok=True)
print(f"📁 Директория плейлистов: {PLAYLISTS_DIR}")

ADMIN_ROLE_NAMES = ['Admin', 'Administrator', 'Модератор', 'Moderator']
BOT_OWNER_ID = int(os.getenv('BOT_OWNER_ID', '0'))

print("✅ Конфигурация успешно загружена!")