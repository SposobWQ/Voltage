import os
import ssl
import random
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')

# SSL фикс
ssl._create_default_https_context = ssl._create_unverified_context
os.environ['PYTHONHTTPSVERIFY'] = '0'

# Проверяем куки файл
COOKIES_LOADED = False
COOKIES_PATH = "youtube_cookies.txt"

def check_cookies_file():
    """Проверяем куки файл в формате Netscape"""
    global COOKIES_LOADED
    try:
        if os.path.exists(COOKIES_PATH):
            with open(COOKIES_PATH, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Проверяем что это Netscape формат
            if '# Netscape HTTP Cookie File' in content:
                # Считаем количество куки (не комментарные строки)
                lines = content.split('\n')
                cookie_count = sum(1 for line in lines if line and not line.startswith('#'))
                
                # Проверяем есть ли важные куки
                important_cookies = ['__Secure-3PSID', '__Secure-3PAPISID', 'LOGIN_INFO']
                found_important = any(any(important in line for line in lines) for important in important_cookies)
                
                if found_important:
                    print(f"✅ Загружено {cookie_count} куки в Netscape формате")
                    COOKIES_LOADED = True
                    return COOKIES_PATH
                else:
                    print("⚠️ Куки файл есть, но важные куки не найдены")
                    return None
            else:
                print("⚠️ Файл куки не в Netscape формате")
                return None
        else:
            print("❌ Файл куки не найден. Возрастные ограничения не будут обходиться.")
            return None
    except Exception as e:
        print(f"❌ Ошибка загрузки куки: {e}")
        return None

COOKIES_FILE = check_cookies_file()

# Случайный User-Agent
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]

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
    'sleep_interval': 1,
    'max_sleep_interval': 2,
    'http_headers': {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-us,en;q=0.5',
        'Accept-Encoding': 'gzip,deflate',
        'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
        'Connection': 'keep-alive',
    },
}

# Добавляем куки если они загружены
if COOKIES_FILE and COOKIES_LOADED:
    YDL_OPTIONS['cookiefile'] = COOKIES_FILE
    print("🎯 Куки активированы - возрастные ограничения будут обходиться")

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

ADMIN_ROLE_NAMES = ['Admin', 'Administrator', 'Модератор', 'Moderator']
BOT_OWNER_ID = int(os.getenv('BOT_OWNER_ID', '0'))

print("✅ Конфигурация загружена")