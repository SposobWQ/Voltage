import os
import ssl
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

# Проверяем куки файл
COOKIES_FILE = 'cookies.txt'
if os.path.exists(COOKIES_FILE):
    file_size = os.path.getsize(COOKIES_FILE)
    print(f"✅ Файл куки найден: {file_size} байт")
else:
    print("⚠️ Файл куки не найден")

# Определяем окружение
IS_RAILWAY = os.getenv('RAILWAY_ENVIRONMENT') is not None or os.getenv('RAILWAY') is not None

# Настройки путей
if IS_RAILWAY:
    PLAYLISTS_DIR = "/app/data/playlists"
else:
    PLAYLISTS_DIR = "./data/playlists"

os.makedirs(PLAYLISTS_DIR, exist_ok=True)
print(f"📁 Директория плейлистов: {PLAYLISTS_DIR}")
print(f"🌐 Окружение: {'Railway' if IS_RAILWAY else 'Локальное'}")

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
}

# Добавляем куки если они загружены
if os.path.exists(COOKIES_FILE):
    YDL_OPTIONS['cookiefile'] = COOKIES_FILE
    print("🎯 Куки активированы")

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -af "volume=0.5"'
}

ADMIN_ROLE_NAMES = ['Admin', 'Administrator', 'Модератор', 'Moderator']
BOT_OWNER_ID = int(os.getenv('BOT_OWNER_ID', '0'))

print("✅ Конфигурация успешно загружена!")