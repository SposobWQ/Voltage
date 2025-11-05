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

# ОБНОВЛЕННЫЕ НАСТРОЙКИ ДЛЯ ОБХОДА ВОЗРАСТНЫХ ОГРАНИЧЕНИЙ
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
    # НАСТРОЙКИ ДЛЯ ОБХОДА ВОЗРАСТНЫХ ОГРАНИЧЕНИЙ
    'age_limit': 100,  # Игнорируем возрастные ограничения
    'extractor_args': {
        'youtube': {
            'player_client': ['android', 'web'],  # Используем мобильные клиенты
            'player_skip': ['configs', 'webpage', 'js'],  # Пропускаем проверки
        }
    },
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-us,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
        'Connection': 'keep-alive',
    }
}

# Улучшенные настройки звука
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -analyzeduration 0 -probesize 32M',
    'options': '-vn -af "volume=1.0" -bufsize 1024k -ac 2 -ar 48000 -b:a 192k'
}

# Настройки качества для разных пресетов
QUALITY_PRESETS = {
    'low': {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn -bufsize 256k -b:a 64k'
    },
    'medium': {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn -bufsize 512k -b:a 128k'
    },
    'high': {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -analyzeduration 0 -probesize 32M',
        'options': '-vn -af "volume=1.0" -bufsize 1024k -ac 2 -ar 48000 -b:a 192k'
    }
}

# Автоматическое определение путей
IS_RAILWAY = os.getenv('RAILWAY_ENVIRONMENT') is not None

def get_playlists_dir():
    railway_volume_path = "/app/data/playlists"
    tmp_path = "/tmp/music_bot/playlists"
    
    os.makedirs(railway_volume_path, exist_ok=True)
    os.makedirs(tmp_path, exist_ok=True)
    
    try:
        test_file = os.path.join(railway_volume_path, "test_write.txt")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        print("✅ Railway volume доступен для записи")
        return railway_volume_path
    except Exception:
        print("⚠️ Railway volume недоступен, используем /tmp")
        return tmp_path

PLAYLISTS_DIR = get_playlists_dir()

# Настройки прав
ADMIN_ROLE_NAMES = ['Admin', 'Administrator', 'Модератор', 'Moderator']
BOT_OWNER_ID = int(os.getenv('BOT_OWNER_ID', '0'))

print(f"✅ Конфигурация загружена с фиксом возрастных ограничений")
print(f"📁 Директория плейлистов: {PLAYLISTS_DIR}")
print(f"🚄 Режим Railway: {IS_RAILWAY}")