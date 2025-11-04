import ssl
import urllib3
import yt_dlp

# Применяем фиксы
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Тестируем
try:
    ydl = yt_dlp.YoutubeDL({'nocheckcertificate': True, 'quiet': True})
    info = ydl.extract_info('ytsearch1:test', download=False)
    print("✅ SSL фикс работает!")
    print(f"Найдено: {info['entries'][0]['title']}")
except Exception as e:
    print(f"❌ Ошибка: {e}")