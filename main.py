import discord
from discord.ext import commands
import os
import asyncio
from config import BOT_TOKEN, IS_RAILWAY

class MusicBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        # Загружаем коги
        await self.load_extension('cogs.music')
        await self.load_extension('cogs.playlist')
        
        # Синхронизируем слэш-команды
        try:
            synced = await self.tree.sync()
            print(f"✅ Синхронизировано {len(synced)} команд")
        except Exception as e:
            print(f"❌ Ошибка синхронизации команд: {e}")

    async def on_ready(self):
        print(f'✅ Бот {self.user} запущен!')
        print(f'📊 ID бота: {self.user.id}')
        print(f'🎵 Количество серверов: {len(self.guilds)}')
        print(f'🚄 Режим: {"Railway" if IS_RAILWAY else "Локальный"}')
        
        # Устанавливаем статус
        activity = discord.Activity(type=discord.ActivityType.listening, name="/play")
        await self.change_presence(activity=activity)

async def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN не найден! Убедитесь, что он установлен в переменных окружения.")
        return
    
    bot = MusicBot()
    
    try:
        await bot.start(BOT_TOKEN)
    except KeyboardInterrupt:
        print("🛑 Бот остановлен")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())