import discord
from discord.ext import commands
import os
import asyncio
import ssl
import subprocess
import sys
import aiohttp
from config import BOT_TOKEN

# Настраиваем вывод логов
print("🚀 Инициализация бота на Railway...")
print(f"🐍 Python version: {sys.version}")
print(f"📁 Working directory: {os.getcwd()}")

# SSL фикс для Railway
ssl._create_default_https_context = ssl._create_unverified_context
os.environ['PYTHONHTTPSVERIFY'] = '0'
print("🔒 SSL фикс активирован")

class MusicBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        
        # Настройки для лучшей стабильности на Railway
        super().__init__(
            command_prefix='!', 
            intents=intents,
            reconnect=True,
            heartbeat_timeout=60.0
        )

    async def setup_hook(self):
        print("🔧 Настройка бота...")
        
        # Проверяем FFmpeg
        try:
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("✅ FFmpeg доступен")
            else:
                print(f"❌ FFmpeg не работает")
        except Exception as e:
            print(f"❌ Ошибка проверки FFmpeg: {e}")

        # Загружаем коги
        try:
            await self.load_extension('cogs.music')
            print("✅ Ког music загружен")
        except Exception as e:
            print(f"❌ Ошибка загрузки music: {e}")

        try:
            await self.load_extension('cogs.playlist')
            print("✅ Ког playlist загружен")
        except Exception as e:
            print(f"❌ Ошибка загрузки playlist: {e}")
        
        # Синхронизируем команды
        try:
            print("🔄 Синхронизация команд с Discord...")
            synced = await self.tree.sync()
            print(f"✅ Синхронизировано {len(synced)} команд")
        except Exception as e:
            print(f"❌ Ошибка синхронизации команд: {e}")

    async def on_ready(self):
        print('=' * 50)
        print(f'🎉 Бот {self.user} запущен на Railway!')
        print(f'🆔 ID бота: {self.user.id}')
        print(f'👥 Бот находится в {len(self.guilds)} серверах')
        print('=' * 50)
        
        activity = discord.Activity(type=discord.ActivityType.listening, name="/play | Railway")
        await self.change_presence(activity=activity)

    async def on_disconnect(self):
        print("🔌 Бот отключен от Discord")

    async def on_resumed(self):
        print("🔁 Соединение с Discord восстановлено")

async def main():
    print("=" * 50)
    print("🚀 ЗАПУСК ДИСКОРД БОТА НА RAILWAY")
    print("=" * 50)
    
    if not BOT_TOKEN:
        print("❌ КРИТИЧЕСКАЯ ОШИБКА: BOT_TOKEN не найден!")
        print("💡 Убедитесь что переменная BOT_TOKEN установлена в Railway Dashboard")
        return
    
    print("✅ BOT_TOKEN найден")
    
    bot = MusicBot()
    
    # Настройки aiohttp для Railway
    connector = aiohttp.TCPConnector(
        limit=100,
        limit_per_host=100,
        ttl_dns_cache=300,
        family=socket.AF_INET  # Принудительно IPv4
    )
    
    try:
        print("🔗 Подключение к Discord...")
        async with aiohttp.ClientSession(connector=connector) as session:
            bot.http.session = session
            await bot.start(BOT_TOKEN)
            
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")
    except discord.LoginFailure:
        print("❌ Ошибка аутентификации: Неверный токен бота")
    except discord.HTTPException as e:
        print(f"❌ HTTP ошибка Discord: {e}")
    except discord.GatewayNotFound as e:
        print(f"❌ Gateway не найден: {e}")
    except discord.ConnectionClosed as e:
        print(f"❌ Соединение закрыто: {e}")
    except Exception as e:
        print(f"❌ Неизвестная ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("👋 Завершение работы бота")
        if not bot.is_closed():
            await bot.close()

if __name__ == "__main__":
    import socket
    
    # Принудительно сбрасываем буфер вывода для Railway
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
    
    # Увеличиваем лимиты для asyncio
    asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Скрипт остановлен")
    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")