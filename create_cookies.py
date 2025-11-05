import json
import os

def create_empty_cookies():
    """Создает пустой файл cookies если он не существует"""
    if not os.path.exists('youtube_cookies.json'):
        empty_cookies = []
        with open('youtube_cookies.json', 'w') as f:
            json.dump(empty_cookies, f)
        print("✅ Создан пустой файл youtube_cookies.json")
        return True
    else:
        print("✅ Файл youtube_cookies.json уже существует")
        return False

if __name__ == "__main__":
    create_empty_cookies()