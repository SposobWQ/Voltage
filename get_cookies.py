import browser_cookie3
import json
import os

def export_youtube_cookies():
    """Экспорт куки из браузера для YouTube"""
    browsers = [
        ('Chrome', browser_cookie3.chrome),
        ('Firefox', browser_cookie3.firefox),
        ('Edge', browser_cookie3.edge),
        ('Opera', browser_cookie3.opera),
        ('Brave', browser_cookie3.brave),
        ('Vivaldi', browser_cookie3.vivaldi),
        ('Safari', browser_cookie3.safari),
    ]
    
    for browser_name, browser_func in browsers:
        try:
            print(f"🔍 Пробуем {browser_name}...")
            cookies = browser_func(domain_name='youtube.com')
            
            if cookies:
                cookie_list = []
                for cookie in cookies:
                    cookie_dict = {
                        'name': cookie.name,
                        'value': cookie.value,
                        'domain': cookie.domain,
                        'path': cookie.path,
                        'expires': cookie.expires,
                        'secure': cookie.secure,
                        'httpOnly': getattr(cookie, 'http_only', False)
                    }
                    cookie_list.append(cookie_dict)
                
                with open('youtube_cookies.json', 'w') as f:
                    json.dump(cookie_list, f, indent=2)
                
                print(f"✅ Куки успешно экспортированы из {browser_name}!")
                print(f"📊 Найдено {len(cookie_list)} куки")
                return
                
        except Exception as e:
            print(f"❌ {browser_name}: {e}")
            continue
    
    print("❌ Не удалось экспортировать куки ни из одного браузера")
    print("\n📝 Альтернативные решения:")
    print("1. Используйте Firefox (проще всего)")
    print("2. Запустите скрипт от администратора")
    print("3. Закройте Chrome перед запуском скрипта")

if __name__ == "__main__":
    export_youtube_cookies()