import browser_cookie3
import os
import time

def export_youtube_cookies_correct():
    """Экспорт куки из браузера в ПРАВИЛЬНОМ Netscape формате"""
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
                    all_cookies.append(cookie)
                print(f"✅ Найдено {len(list(cookies))} cookies в {browser_name}")
                break  # Останавливаемся на первом успешном браузере
                
        except Exception as e:
            print(f"❌ {browser_name}: {e}")
            continue
    
    if all_cookies:
        # Создаем Netscape формат ПРАВИЛЬНО
        netscape_lines = [
            "# Netscape HTTP Cookie File",
            "# https://curl.haxx.se/rfc/cookie_spec.html", 
            "# This is a generated file! Do not edit.",
            ""
        ]
        
        valid_cookies = 0
        invalid_cookies = 0
        
        for cookie in all_cookies:
            try:
                # Форматируем правильно
                domain = cookie.domain
                if not domain.startswith('.'):
                    domain = '.' + domain
                
                domain_specified = 'TRUE'  # Всегда TRUE для .domain
                path = cookie.path if cookie.path else '/'
                secure = 'TRUE' if cookie.secure else 'FALSE'
                
                # expires должно быть числом или 0
                if cookie.expires and cookie.expires > 0:
                    expires = str(int(cookie.expires))
                else:
                    expires = '0'
                
                name = cookie.name
                value = cookie.value
                
                # Проверяем что все поля валидны
                if not all([domain, path, name, value]):
                    invalid_cookies += 1
                    continue
                
                netscape_line = f"{domain}\t{domain_specified}\t{path}\t{secure}\t{expires}\t{name}\t{value}"
                netscape_lines.append(netscape_line)
                valid_cookies += 1
                
            except Exception as e:
                print(f"⚠️ Ошибка обработки куки {cookie.name}: {e}")
                invalid_cookies += 1
                continue
        
        # Сохраняем в файл
        with open('youtube_cookies_correct.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(netscape_lines))
        
        print(f"🎉 Успешно экспортировано {valid_cookies} cookies!")
        if invalid_cookies > 0:
            print(f"🚫 Пропущено {invalid_cookies} невалидных cookies")
        print("📁 Файл: youtube_cookies_correct.txt")
        
        # Показываем важные куки
        important_cookies = ['__Secure-3PSID', '__Secure-3PAPISID', 'LOGIN_INFO']
        found = []
        for cookie in all_cookies:
            if cookie.name in important_cookies:
                found.append(cookie.name)
        
        print(f"🔑 Найдено важных cookies: {', '.join(found)}")
        
        if found:
            print("✅ Cookies готовы к использованию в yt-dlp!")
        else:
            print("⚠️ Важные cookies не найдены. Убедитесь что вы залогинены в YouTube.")
        
        return True
    else:
        print("❌ Не удалось найти cookies ни в одном браузере")
        return False

if __name__ == "__main__":
    export_youtube_cookies_correct()