import os
import re

def fix_cookies_file():
    """Исправляет куки файл в правильный Netscape формат"""
    input_file = 'youtube_cookies.txt'
    output_file = 'youtube_cookies_fixed.txt'
    
    print("🔧 Исправление куки файла...")
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        fixed_lines = []
        skipped_count = 0
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Пропускаем пустые строки и комментарии
            if not line or line.startswith('#'):
                fixed_lines.append(line)
                continue
            
            # Разбираем строку куки
            parts = line.split('\t')
            
            if len(parts) != 7:
                print(f"⚠️ Строка {line_num}: неверное количество полей ({len(parts)}), пропускаем")
                skipped_count += 1
                continue
            
            domain, domain_specified, path, secure, expires, name, value = parts
            
            # Исправляем domain_specified
            if domain_specified.upper() not in ['TRUE', 'FALSE']:
                domain_specified = 'TRUE' if domain.startswith('.') else 'FALSE'
                print(f"🔧 Строка {line_num}: исправлен domain_specified на {domain_specified}")
            
            # Исправляем secure
            if secure.upper() not in ['TRUE', 'FALSE']:
                secure = 'FALSE'
                print(f"🔧 Строка {line_num}: исправлен secure на {secure}")
            
            # Проверяем expires - должно быть число или 0
            try:
                if expires == 'None' or not expires.strip():
                    expires = '0'
                    print(f"🔧 Строка {line_num}: исправлен expires на 0")
                else:
                    int(expires)  # Проверяем что это число
            except (ValueError, TypeError):
                expires = '0'
                print(f"🔧 Строка {line_num}: исправлен expires на 0")
            
            # Собираем исправленную строку
            fixed_line = f"{domain}\t{domain_specified}\t{path}\t{secure}\t{expires}\t{name}\t{value}"
            fixed_lines.append(fixed_line)
        
        # Сохраняем исправленный файл
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(fixed_lines))
        
        print(f"✅ Файл исправлен: {output_file}")
        print(f"📊 Обработано строк: {len(lines)}")
        print(f"🚫 Пропущено строк: {skipped_count}")
        print(f"💾 Сохранено строк: {len(fixed_lines)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка исправления файла: {e}")
        return False

def validate_cookies_file(filename):
    """Проверяет валидность куки файла"""
    print(f"🔍 Проверка файла {filename}...")
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        valid_count = 0
        invalid_count = 0
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            parts = line.split('\t')
            if len(parts) != 7:
                print(f"❌ Строка {line_num}: неверное количество полей")
                invalid_count += 1
                continue
            
            domain, domain_specified, path, secure, expires, name, value = parts
            
            # Проверяем поля
            errors = []
            if domain_specified.upper() not in ['TRUE', 'FALSE']:
                errors.append(f"domain_specified: {domain_specified}")
            
            if secure.upper() not in ['TRUE', 'FALSE']:
                errors.append(f"secure: {secure}")
            
            try:
                if expires != '0':
                    int(expires)
            except (ValueError, TypeError):
                errors.append(f"expires: {expires}")
            
            if errors:
                print(f"⚠️ Строка {line_num}: {', '.join(errors)}")
                invalid_count += 1
            else:
                valid_count += 1
        
        print(f"📊 Результат проверки {filename}:")
        print(f"✅ Валидных куки: {valid_count}")
        print(f"❌ Невалидных куки: {invalid_count}")
        
        return valid_count > 0
        
    except Exception as e:
        print(f"❌ Ошибка проверки файла: {e}")
        return False

if __name__ == "__main__":
    print("🛠️ Исправление куки файла...")
    
    if not os.path.exists('youtube_cookies.txt'):
        print("❌ Файл youtube_cookies.txt не найден!")
        print("💡 Сначала запусти get_cookies.py")
        exit(1)
    
    # Проверяем исходный файл
    print("📋 Проверка исходного файла:")
    original_valid = validate_cookies_file('youtube_cookies.txt')
    
    if not original_valid:
        print("🔧 Исправляем файл...")
        if fix_cookies_file():
            print("📋 Проверка исправленного файла:")
            validate_cookies_file('youtube_cookies_fixed.txt')
            print("🎉 Файл исправлен! Используйте youtube_cookies_fixed.txt")
        else:
            print("💥 Не удалось исправить файл")
    else:
        print("✅ Исходный файл валиден!")