#!/usr/bin/env python3
import os
import sys
import asyncio
import time
import subprocess
from railway_fix import apply_railway_fixes, test_discord_connection

def check_environment():
    """Проверяет окружение"""
    print("🔍 Проверка окружения...")
    
    # Проверяем переменные
    required_vars = ['BOT_TOKEN']
    for var in required_vars:
        if not os.getenv(var):
            print(f"❌ Отсутствует переменная: {var}")
            return False
    
    print("✅ Все переменные окружения на месте")
    return True

async def start_bot_with_retry():
    """Запускает бота с повторными попытками"""
    max_retries = 10  # Увеличиваем количество попыток
    retry_delay = 10  # Начинаем с 10 секунд
    
    for attempt in range(max_retries):
        print(f"🔄 Попытка запуска {attempt + 1}/{max_retries}...")
        
        # Тестируем подключение перед запуском
        if await test_discord_connection():
            try:
                # Запускаем основной скрипт
                from main import main
                await main()
                break
                
            except Exception as e:
                print(f"❌ Попытка {attempt + 1} не удалась: {e}")
        else:
            print(f"❌ Не удалось подключиться к Discord, попытка {attempt + 1}")
            
        if attempt < max_retries - 1:
            print(f"⏳ Повторная попытка через {retry_delay} секунд...")
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 1.5, 120)  # Экспоненциальная задержка, максимум 2 минуты
        else:
            print("💥 Все попытки запуска провалились")
            sys.exit(1)

async def health_check():
    """Простой health check в фоне"""
    while True:
        await asyncio.sleep(60)
        print("💓 Health check: бот жив")

async def main():
    print("=" * 50)
    print("🎵 ЗАПУСК ДИСКОРД БОТА (УСИЛЕННАЯ ВЕРСИЯ)")
    print("=" * 50)
    
    # Применяем фиксы
    apply_railway_fixes()
    
    # Проверяем окружение
    if not check_environment():
        print("❌ Не удалось запустить бота: проблемы с окружением")
        sys.exit(1)
    
    # Запускаем health check в фоне
    health_task = asyncio.create_task(health_check())
    
    # Запускаем бота с повторными попытками
    await start_bot_with_retry()
    
    # Отменяем health check при завершении
    health_task.cancel()

if __name__ == "__main__":
    # Устанавливаем более стабильные настройки asyncio
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    else:
        asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")
    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")
        sys.exit(1)