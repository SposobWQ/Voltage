import discord
from discord.ext import commands
import os
import asyncio
import ssl
import sys
from config import BOT_TOKEN
import aiohttp

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
        
        # Кастомные настройки HTTP
        http_client = discord.http.HTTPClient()
        http_client._session = self.create_custom_session()
        
        super().__init__(
            command_prefix='!', 
            intents=intents,
            reconnect=True,
            http_client=http_client
        )

    def create_custom_session(self):
        """Создает кастомную сессию с увеличенными таймаутами"""
        timeout = aiohttp.ClientTimeout(total=60, connect=30, sock_connect=30, sock_read=60)
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=30,
            keepalive_timeout=30,
            enable_cleanup_closed=True,
            use_dns_cache=True,
            verify_ssl=False
        )
        return aiohttp.ClientSession(timeout=timeout, connector=connector)

    async def setup_hook(self):
        print("🔧 Настройка бота...")
        
        # Проверяем существование файлов когов
        print("🔍 Проверка файлов когов...")
        cog_files = ['cogs/music.py', 'cogs/playlist.py']
        for cog_file in cog_files:
            if os.path.exists(cog_file):
                print(f"✅ {cog_file} найден")
            else:
                print(f"❌ {cog_file} не найден!")
        
        # Загружаем коги с детальными логами
        try:
            await self.load_extension('cogs.music')
            print("✅ Ког music загружен")
        except Exception as e:
            print(f"❌ Ошибка загрузки music: {e}")
            import traceback
            traceback.print_exc()

        try:
            await self.load_extension('cogs.playlist')
            print("✅ Ког playlist загружен")
        except Exception as e:
            print(f"❌ Ошибка загрузки playlist: {e}")
            import traceback
            traceback.print_exc()
        
        # Синхронизируем команды
        try:
            print("🔄 Синхронизация команд с Discord...")
            synced = await self.tree.sync()
            print(f"✅ Синхронизировано {len(synced)} команд")
            
            # Выводим список всех команд для отладки
            command_list = [cmd.name for cmd in synced]
            print(f"📋 Все команды: {', '.join(command_list)}")
            
        except Exception as e:
            print(f"❌ Ошибка синхронизации команд: {e}")
            import traceback
            traceback.print_exc()

    async def on_ready(self):
        print('=' * 50)
        print(f'🎉 Бот {self.user} запущен на Railway!')
        print(f'🆔 ID бота: {self.user.id}')
        print(f'👥 Бот находится в {len(self.guilds)} серверах')
        print('=' * 50)
        
        activity = discord.Activity(type=discord.ActivityType.listening, name="/play | Railway")
        await self.change_presence(activity=activity)

    async def close(self):
        """Корректное закрытие сессии"""
        if hasattr(self.http, '_session') and self.http._session:
            await self.http._session.close()
        await super().close()

async def main():
    print("=" * 50)
    print("🚀 ЗАПУСК ДИСКОРД БОТА НА RAILWAY")
    print("=" * 50)
    
    if not BOT_TOKEN:
        print("❌ КРИТИЧЕСКАЯ ОШИБКА: BOT_TOKEN не найден!")
        return
    
    print("✅ BOT_TOKEN найден")
    
    bot = MusicBot()
    
    try:
        print("🔗 Подключение к Discord...")
        await bot.start(BOT_TOKEN)
            
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("👋 Завершение работы бота")
        if not bot.is_closed():
            await bot.close()

if __name__ == "__main__":
    # Принудительно сбрасываем буфер вывода для Railway
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
    
    # Увеличиваем лимиты asyncio
    asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Скрипт остановлен")
    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")