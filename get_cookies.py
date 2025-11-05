import browser_cookie3
import json
import os

def export_youtube_cookies():
    """Экспорт куки из браузера для YouTube"""
    print("🔍 Поиск YouTube cookies в браузерах...")
    
    browsers = [
        ('Chrome', browser_cookie3.chrome),
        ('Firefox', browser_cookie3.firefox),
        ('Edge', browser_cookie3.edge),
        ('Opera', browser_cookie3.opera),
        ('Brave', browser_cookie3.brave),
    ]
    
    all_cookies = []
    
    for browser_name, browser_func in browsers:
        try:
            print(f"🔍 Проверяем {browser_name}...")
            cookies = browser_func(domain_name='youtube.com')
            
            if cookies:
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
                    all_cookies.append(cookie_dict)
                
                print(f"✅ Найдено {len(list(cookies))} cookies в {browser_name}")
                break  # Останавливаемся на первом успешном браузере
                
        except Exception as e:
            print(f"❌ {browser_name}: {e}")
            continue
    
    if all_cookies:
        # Сохраняем в файл
        with open('youtube_cookies.json', 'w', encoding='utf-8') as f:
            json.dump(all_cookies, f, indent=2, ensure_ascii=False)
        
        print(f"🎉 Успешно экспортировано {len(all_cookies)} cookies!")
        print("📁 Файл: youtube_cookies.json")
        
        # Показываем важные куки
        important_cookies = ['__Secure-3PSID', '__Secure-3PAPISID', 'LOGIN_INFO']
        found = []
        for cookie in all_cookies:
            if cookie['name'] in important_cookies:
                found.append(cookie['name'])
        
        print(f"🔑 Найдено важных cookies: {', '.join(found)}")
        
        if found:
            print("✅ Cookies готовы к использованию!")
        else:
            print("⚠️ Важные cookies не найдены. Убедитесь что вы залогинены в YouTube.")
        
        return True
    else:
        print("❌ Не удалось найти cookies ни в одном браузере")
        print("\n💡 Решения:")
        print("1. Убедитесь что вы залогинены в YouTube в браузере")
        print("2. Попробуйте запустить скрипт от администратора")
        print("3. Закройте браузер перед запуском скрипта")
        print("4. Попробуйте другой браузер")
        return False

if __name__ == "__main__":
    export_youtube_cookies()