import yt_dlp
import os

def test_cookies_with_ytdlp():
    """Тестирует куки файл с yt-dlp"""
    print("🧪 Тестирование куки с yt-dlp...")
    
    if not os.path.exists('cookies.txt'):
        print("❌ Файл cookies.txt не найден!")
        return False
    
    # Тестовое видео (обычное, без ограничений)
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Astley
    
    ydl_opts = {
        'cookiefile': 'cookies.txt',
        'quiet': True,
        'no_warnings': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("🔗 Тестируем подключение...")
            info = ydl.extract_info(test_url, download=False)
            
        print("✅ Куки работают правильно!")
        print(f"📹 Видео: {info.get('title', 'Unknown')}")
        print(f"⏱️ Длительность: {info.get('duration', 'Unknown')} сек")
        return True
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Ошибка: {error_msg}")
        
        if "cookies" in error_msg.lower():
            print("💡 Проблема с куки файлом")
        elif "age" in error_msg.lower():
            print("💡 Возрастное ограничение - куки не работают")
        else:
            print("💡 Другая ошибка")
        
        return False

if __name__ == "__main__":
    test_cookies_with_ytdlp()