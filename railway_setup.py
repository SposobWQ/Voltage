import os
import json

def setup_railway():
    """Настройка окружения для Railway"""
    print("🚄 Настройка Railway окружения...")
    
    # Проверяем переменные окружения
    required_vars = ['BOT_TOKEN']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Отсутствуют переменные окружения: {', '.join(missing_vars)}")
        print("💡 Установите их в Railway Dashboard -> Variables")
        return False
    
    print("✅ Все необходимые переменные окружения установлены")
    
    # Проверяем и создаем директории
    directories = ['./data', './data/playlists', './data/backups']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Создана директория: {directory}")
    
    # Проверяем cookies
    if os.path.exists('youtube_cookies.json'):
        try:
            with open('youtube_cookies.json', 'r') as f:
                cookies = json.load(f)
            print(f"✅ Файл cookies найден: {len(cookies)} cookies")
        except Exception as e:
            print(f"❌ Ошибка чтения cookies: {e}")
    else:
        print("⚠️ Файл cookies не найден. Возрастные ограничения не будут обходиться.")
    
    print("🎉 Настройка Railway завершена!")
    return True

if __name__ == "__main__":
    setup_railway()