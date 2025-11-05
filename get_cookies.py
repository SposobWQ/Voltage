import browser_cookie3
import os
import time

def create_perfect_cookies():
    """Создает идеально отформатированный куки файл"""
    print("🎯 Создание правильного куки файла...")
    
    browsers = [
        ('Chrome', browser_cookie3.chrome),
        ('Firefox', browser_cookie3.firefox),
        ('Edge', browser_cookie3.edge),
        ('Opera', browser_cookie3.opera),
        ('Brave', browser_cookie3.brave),
    ]
    
    # Собираем все куки
    all_cookies = []
    browser_used = None
    
    for browser_name, browser_func in browsers:
        try:
            print(f"🔍 Проверяем {browser_name}...")
            cookies = list(browser_func(domain_name='youtube.com'))
            
            if cookies:
                print(f"✅ Найдено {len(cookies)} cookies в {browser_name}")
                all_cookies.extend(cookies)
                browser_used = browser_name
                break
        except Exception as e:
            print(f"❌ {browser_name}: {e}")
            continue
    
    if not all_cookies:
        print("❌ Не удалось найти cookies ни в одном браузере")
        return False
    
    print(f"🎯 Используем куки из {browser_used}")
    
    # Создаем ПРАВИЛЬНЫЙ Netscape формат
    header = """# Netscape HTTP Cookie File
# https://curl.haxx.se/rfc/cookie_spec.html
# This is a generated file! Do not edit.

"""
    
    perfect_lines = [header]
    valid_count = 0
    invalid_count = 0
    
    for cookie in all_cookies:
        try:
            # ОБЯЗАТЕЛЬНО: domain должен начинаться с точки
            domain = cookie.domain
            if not domain.startswith('.'):
                domain = '.' + domain
            
            # ОБЯЗАТЕЛЬНО: domain_specified должен быть TRUE если domain начинается с точки
            domain_specified = 'TRUE'
            
            # path не может быть пустым
            path = cookie.path if cookie.path and cookie.path.strip() else '/'
            
            # secure должен быть TRUE или FALSE
            secure = 'TRUE' if cookie.secure else 'FALSE'
            
            # expires ДОЛЖНО быть числом или 0, не может быть None
            if cookie.expires and cookie.expires > 0:
                expires = str(int(cookie.expires))
            else:
                expires = '0'  # Если нет expires, ставим 0
            
            name = cookie.name
            value = cookie.value
            
            # Проверяем что все поля заполнены
            if not all([domain, path, name, value]):
                invalid_count += 1
                continue
            
            # Собираем строку в ПРАВИЛЬНОМ формате
            cookie_line = f"{domain}\t{domain_specified}\t{path}\t{secure}\t{expires}\t{name}\t{value}"
            perfect_lines.append(cookie_line)
            valid_count += 1
            
        except Exception as e:
            print(f"⚠️ Ошибка с куки {getattr(cookie, 'name', 'unknown')}: {e}")
            invalid_count += 1
            continue
    
    # Сохраняем в файл
    output_file = 'cookies.txt'
    with open(output_file, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(perfect_lines))
    
    print(f"✅ Создан файл: {output_file}")
    print(f"📊 Статистика:")
    print(f"   ✅ Валидных куки: {valid_count}")
    print(f"   ❌ Невалидных куки: {invalid_count}")
    print(f"   📁 Размер файла: {os.path.getsize(output_file)} байт")
    
    # Проверяем важные куки
    important_found = []
    for cookie in all_cookies:
        name = getattr(cookie, 'name', '')
        if any(important in name for important in ['__Secure-3PSID', '__Secure-3PAPISID', 'LOGIN_INFO']):
            important_found.append(name)
    
    if important_found:
        print(f"🔑 Важные куки найдены: {', '.join(set(important_found))}")
    else:
        print("⚠️ Важные куки не найдены!")
    
    return True

def test_cookies_file():
    """Тестирует созданный файл"""
    print("\n🧪 Тестирование файла куки...")
    
    try:
        import http.cookiejar as cookielib
        
        # Создаем куки-джар и загружаем файл
        cj = cookielib.MozillaCookieJar()
        cj.load('cookies.txt', ignore_discard=True, ignore_expires=True)
        
        print(f"✅ Файл успешно загружен!")
        print(f"🍪 Загружено куки: {len(cj)}")
        
        # Показываем несколько куки для проверки
        print("\n🔍 Примеры куки:")
        for i, cookie in enumerate(list(cj)[:3]):
            print(f"   {i+1}. {cookie.name} = {cookie.value[:20]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🛠️ СОЗДАНИЕ ИДЕАЛЬНОГО КУКИ ФАЙЛА")
    print("=" * 50)
    
    if create_perfect_cookies():
        print("\n" + "=" * 50)
        test_cookies_file()
        print("=" * 50)
        print("🎉 Файл cookies.txt готов к использованию!")
    else:
        print("💥 Не удалось создать куки файл")