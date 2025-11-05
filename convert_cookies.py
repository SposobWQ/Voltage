import json
import os

def convert_json_to_netscape():
    """Конвертирует куки из JSON в формат Netscape"""
    try:
        # Читаем JSON файл
        with open('youtube_cookies.json', 'r', encoding='utf-8') as f:
            cookies = json.load(f)
        
        # Создаем Netscape формат
        netscape_lines = [
            "# Netscape HTTP Cookie File",
            "# https://curl.haxx.se/rfc/cookie_spec.html",
            "# This is a generated file! Do not edit.",
            ""
        ]
        
        for cookie in cookies:
            # Форматируем по стандарту Netscape
            domain = cookie.get('domain', '.youtube.com').lstrip('.')
            if not domain.startswith('.'):
                domain = '.' + domain
            
            flag = 'TRUE' if cookie.get('secure') else 'FALSE'
            path = cookie.get('path', '/')
            secure = 'TRUE' if cookie.get('secure') else 'FALSE'
            expires = str(cookie.get('expires', '0'))
            name = cookie.get('name', '')
            value = cookie.get('value', '')
            
            netscape_line = f"{domain}\t{flag}\t{path}\t{secure}\t{expires}\t{name}\t{value}"
            netscape_lines.append(netscape_line)
        
        # Сохраняем в Netscape формате
        with open('youtube_cookies.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(netscape_lines))
        
        print(f"✅ Конвертировано {len(cookies)} куки в Netscape формат")
        print("📁 Создан файл: youtube_cookies.txt")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка конвертации: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Конвертация куки в Netscape формат...")
    if convert_json_to_netscape():
        print("🎉 Конвертация успешна!")
    else:
        print("💥 Конвертация не удалась!")