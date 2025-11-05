import os
import ssl
import json
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')

# SSL фикс
ssl._create_default_https_context = ssl._create_unverified_context
os.environ['PYTHONHTTPSVERIFY'] = '0'

# Пытаемся загрузить куки
COOKIES_LOADED = False
COOKIES_PATH = "youtube_cookies.json"

def load_cookies():
    """Загрузка куки из файла"""
    global COOKIES_LOADED
    try:
        if os.path.exists(COOKIES_PATH):
            with open(COOKIES_PATH, 'r') as f:
                cookies = json.load(f)
            print(f"✅ Загружено {len(cookies)} куки для YouTube")
            COOKIES_LOADED = True
            return COOKIES_PATH
        else:
            print("⚠️ Файл куки не найден. Возрастные ограничения не будут обходиться.")
            return None
    except Exception as e:
        print(f"❌ Ошибка загрузки куки: {e}")
        return None

COOKIES_FILE = load_cookies()

# НАСТРОЙКИ С ПОДДЕРЖКОЙ КУКИ
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': False,
    'nocheckcertificate': True,
    'ignoreerrors': True,  # Игнорируем ошибки для стабильности
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'extract_flat': False,
    'ssl_verify': False,
    'geo_bypass': True,
    'socket_timeout': 30,
    'buffersize': 2048,
    'extractor_args': {
        'youtube': {
            'player_client': ['android', 'ios', 'web'],
            'player_skip': ['configs', 'webpage', 'js'],
        }
    },
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-us,en;q=0.5',
        'Accept-Encoding': 'gzip,deflate',
        'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
    },
    'age_limit': 100,  # Игнорируем возрастные ограничения
}

# Добавляем куки если они есть
if COOKIES_FILE:
    YDL_OPTIONS['cookiefile'] = COOKIES_FILE
    print("🎯 Куки активированы - возрастные ограничения будут обходиться")

# НАСТРОЙКИ КАЧЕСТВА
QUALITY_PRESETS = {
    'low': {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -probesize 32 -analyzeduration 0',
        'options': '-vn -af "volume=1.0" -bufsize 512k -ac 2 -ar 44100 -b:a 64k'
    },
    'medium': {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -probesize 32 -analyzeduration 0', 
        'options': '-vn -af "volume=1.0" -bufsize 1024k -ac 2 -ar 48000 -b:a 128k'
    },
    'high': {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -probesize 32 -analyzeduration 0',
        'options': '-vn -af "volume=1.0" -bufsize 2048k -ac 2 -ar 48000 -b:a 192k'
    }
}

FFMPEG_OPTIONS = QUALITY_PRESETS['medium']  # Среднее качество по умолчанию для экономии трафика

# НАСТРОЙКИ ПУТЕЙ ДЛЯ RAILWAY
if os.getenv('RAILWAY_ENVIRONMENT'):
    PLAYLISTS_DIR = "/app/data/playlists"
    print("🚄 Режим Railway: используем persistent storage")
else:
    PLAYLISTS_DIR = "./data/playlists"
    print("💻 Локальный режим: используем локальную директорию")

os.makedirs(PLAYLISTS_DIR, exist_ok=True)

ADMIN_ROLE_NAMES = ['Admin', 'Administrator', 'Модератор', 'Moderator']
BOT_OWNER_ID = int(os.getenv('BOT_OWNER_ID', '0'))
IS_RAILWAY = os.getenv('RAILWAY_ENVIRONMENT') is not None

print("✅ Конфигурация загружена")