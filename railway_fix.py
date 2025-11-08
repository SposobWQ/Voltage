import os
import asyncio
import aiohttp
import socket
import urllib3

def apply_railway_fixes():
    """Применяет фиксы для Railway"""
    print("🔧 Применение фиксов для Railway...")
    
    # Отключаем проверки SSL для избежания проблем с сертификатами
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Увеличиваем таймауты
    os.environ['AIOHTTP_NO_EXTENSIONS'] = '1'
    os.environ['PYTHONUNBUFFERED'] = '1'
    
    # Настройки для DNS
    socket.setdefaulttimeout(30)
    
    print("✅ Фиксы применены")

async def test_discord_connection():
    """Тестирует подключение к Discord"""
    print("🔗 Тестирование подключения к Discord...")
    
    try:
        # Создаем кастомную сессию с увеличенными таймаутами
        timeout = aiohttp.ClientTimeout(total=60, connect=30, sock_connect=30, sock_read=60)
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=30,
            keepalive_timeout=30,
            enable_cleanup_closed=True,
            use_dns_cache=True
        )
        
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            async with session.get('https://discord.com/api/v10/users/@me', 
                                 headers={'Authorization': f'Bot {os.getenv("BOT_TOKEN")}'}) as response:
                if response.status == 200:
                    print("✅ Подключение к Discord успешно!")
                    return True
                else:
                    print(f"❌ Ошибка Discord API: {response.status}")
                    return False
                    
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

if __name__ == "__main__":
    apply_railway_fixes()
    asyncio.run(test_discord_connection())