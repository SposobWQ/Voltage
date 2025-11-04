import discord
from discord.ext import commands
import os
import asyncio
import ssl
from config import BOT_TOKEN

# SSL фикс
ssl._create_default_https_context = ssl._create_unverified_context
os.environ['PYTHONHTTPSVERIFY'] = '0'

class MusicBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
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
        print('🔒 SSL фикс активирован')
        
        activity = discord.Activity(type=discord.ActivityType.listening, name="/play | Качество: high")
        await self.change_presence(activity=activity)

async def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN не найден!")
        return
    
    print("🚀 Запуск бота с улучшенным качеством звука...")
    bot = MusicBot()
    
    try:
        await bot.start(BOT_TOKEN)
    except KeyboardInterrupt:
        print("🛑 Бот остановлен")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())