import os
import ssl
import json
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')

# SSL фикс
ssl._create_default_https_context = ssl._create_unverified_context
os.environ['PYTHONHTTPSVERIFY'] = '0'

# Проверяем куки файл
COOKIES_LOADED = False
COOKIES_PATH = "youtube_cookies.json"

def check_cookies_file():
    """Проверяем и загружаем куки файл"""
    global COOKIES_LOADED
    try:
        if os.path.exists(COOKIES_PATH):
            with open(COOKIES_PATH, 'r') as f:
                cookies = json.load(f)
            
            if isinstance(cookies, list) and len(cookies) > 0:
                # Проверяем есть ли важные куки
                important_cookies = ['__Secure-3PSID', '__Secure-3PAPISID', 'LOGIN_INFO']
                found_important = any(any(cookie.get('name') == important for cookie in cookies) for important in important_cookies)
                
                if found_important:
                    print(f"✅ Загружено {len(cookies)} куки, важные куки найдены")
                    COOKIES_LOADED = True
                    return COOKIES_PATH
                else:
                    print("⚠️ Куки файл есть, но важные куки не найдены")
                    return None
            else:
                print("⚠️ Куки файл пустой или неверного формата")
                return None
        else:
            print("❌ Файл куки не найден. Возрастные ограничения не будут обходиться.")
            return None
    except Exception as e:
        print(f"❌ Ошибка загрузки куки: {e}")
        return None

COOKIES_FILE = check_cookies_file()

# НАСТРОЙКИ YT-DLP
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
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
    'socket_timeout': 30,
    'buffersize': 2048,
}

# Добавляем куки если они загружены
if COOKIES_FILE and COOKIES_LOADED:
    YDL_OPTIONS['cookiefile'] = COOKIES_FILE
    print("🎯 Куки активированы - возрастные ограничения будут обходиться")

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -probesize 32 -analyzeduration 0',
    'options': '-vn -af "volume=0.5" -bufsize 1024k'
}

# Настройки путей
if os.getenv('RAILWAY_ENVIRONMENT'):
    PLAYLISTS_DIR = "/app/data/playlists"
    print("🚄 Режим Railway: используем persistent storage")
else:
    PLAYLISTS_DIR = "./data/playlists"
    print("💻 Локальный режим")

os.makedirs(PLAYLISTS_DIR, exist_ok=True)

ADMIN_ROLE_NAMES = ['Admin', 'Administrator', 'Модератор', 'Moderator']
BOT_OWNER_ID = int(os.getenv('BOT_OWNER_ID', '0'))

print("✅ Конфигурация загружена")