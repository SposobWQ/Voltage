import discord
from discord.ext import commands
import os
import asyncio
import ssl
import subprocess
from config import BOT_TOKEN

# SSL фикс
ssl._create_default_https_context = ssl._create_unverified_context
os.environ['PYTHONHTTPSVERIFY'] = '0'

class MusicBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(
            command_prefix='!', 
            intents=intents,
            reconnect=True
        )

    async def setup_hook(self):
        print("🔧 Настройка бота...")
        
        # Проверяем FFmpeg
        try:
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("✅ FFmpeg доступен")
                # Выводим версию FFmpeg
                version_line = result.stdout.split('\n')[0]
                print(f"📀 {version_line}")
            else:
                print("❌ FFmpeg не работает")
        except subprocess.TimeoutExpired:
            print("❌ Таймаут проверки FFmpeg")
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
            synced = await self.tree.sync()
            print(f"✅ Синхронизировано {len(synced)} команд")
        except Exception as e:
            print(f"❌ Ошибка синхронизации команд: {e}")

    async def on_ready(self):
        print(f'🎉 Бот {self.user} запущен и готов к работе!')
        print(f'🆔 ID бота: {self.user.id}')
        print(f'👥 Бот находится в {len(self.guilds)} серверах')
        
        # Показываем информацию о серверах
        for guild in self.guilds:
            print(f'   - {guild.name} (ID: {guild.id})')
        
        activity = discord.Activity(type=discord.ActivityType.listening, name="/play | /help")
        await self.change_presence(activity=activity)
        print("🎵 Статус активности установлен")

    async def on_guild_join(self, guild):
        print(f'➕ Бот добавлен на сервер: {guild.name} (ID: {guild.id})')

    async def on_guild_remove(self, guild):
        print(f'➖ Бот удален с сервера: {guild.name} (ID: {guild.id})')

async def main():
    print("=" * 50)
    print("🚀 ЗАПУСК ДИСКОРД БОТА")
    print("=" * 50)
    
    if not BOT_TOKEN:
        print("❌ КРИТИЧЕСКАЯ ОШИБКА: BOT_TOKEN не найден!")
        print("💡 Убедитесь что переменная BOT_TOKEN установлена в Railway Dashboard")
        return
    
    print("✅ BOT_TOKEN найден")
    
    bot = MusicBot()
    
    try:
        print("🔗 Подключение к Discord...")
        await bot.start(BOT_TOKEN)
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")
    except discord.LoginFailure:
        print("❌ Ошибка аутентификации: Неверный токен бота")
    except discord.PrivilegedIntentsRequired:
        print("❌ Ошибка: Privileged Intents не включены в Discord Developer Portal")
    except Exception as e:
        print(f"❌ Неизвестная ошибка: {e}")
    finally:
        print("👋 Завершение работы бота")

if __name__ == "__main__":
    # Устанавливаем кодировку для корректного вывода логов
    import sys
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    asyncio.run(main())