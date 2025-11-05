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
        
        # Настройки для избежания блокировки
        super().__init__(
            command_prefix='!', 
            intents=intents,
            reconnect=True
        )

    async def setup_hook(self):
        # Проверяем FFmpeg
        try:
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ FFmpeg доступен")
            else:
                print("❌ FFmpeg не работает")
        except:
            print("❌ FFmpeg не установлен")

        try:
            await self.load_extension('cogs.music')
            await self.load_extension('cogs.playlist')
            print("✅ Коги загружены")
        except Exception as e:
            print(f"❌ Ошибка загрузки когов: {e}")
        
        try:
            synced = await self.tree.sync()
            print(f"✅ Синхронизировано {len(synced)} команд")
        except Exception as e:
            print(f"❌ Ошибка синхронизации команд: {e}")

    async def on_ready(self):
        print(f'✅ Бот {self.user} запущен!')
        print(f'📊 ID бота: {self.user.id}')
        
        activity = discord.Activity(type=discord.ActivityType.listening, name="/play | Stable")
        await self.change_presence(activity=activity)

    async def on_error(self, event, *args, **kwargs):
        print(f"❌ Ошибка в событии {event}: {args} {kwargs}")

async def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN не найден!")
        return
    
    print("🚀 Запуск бота с защитой от блокировки...")
    bot = MusicBot()
    
    try:
        await bot.start(BOT_TOKEN)
    except KeyboardInterrupt:
        print("🛑 Бот остановлен вручную")
    except discord.HTTPException as e:
        if e.status == 429:
            print("🚫 Слишком много запросов к Discord. Ждем 1 минуту...")
            await asyncio.sleep(60)
            await main()  # Перезапускаем
        else:
            print(f"❌ Ошибка Discord: {e}")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        print("🔄 Перезапуск через 30 секунд...")
        await asyncio.sleep(30)
        await main()  # Перезапускаем

if __name__ == "__main__":
    asyncio.run(main())