import os
import time
import subprocess
import sys

def restart_bot():
    """Перезапускает бота при ошибках"""
    print("🔄 Перезапуск бота из-за ошибки...")
    time.sleep(10)  # Ждем 10 секунд перед перезапуском
    os.execv(sys.executable, ['python'] + sys.argv)

if __name__ == "main":
    try:
        # Запускаем основной бот
        subprocess.run([sys.executable, 'main.py'])
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        restart_bot()