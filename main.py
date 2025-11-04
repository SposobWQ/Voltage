import discord
from discord.ext import commands
import os
from config import BOT_TOKEN, PREFIX

class MusicBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix=PREFIX, intents=intents)

    async def setup_hook(self):
        # Загружаем коги
        await self.load_extension('cogs.music')
        await self.load_extension('cogs.playlist')
        
        # Синхронизируем слэш-команды
        await self.tree.sync()
        print("✅ Слэш-команды синхронизированы")

    async def on_ready(self):
        print(f'✅ Бот {self.user} запущен!')
        print(f'📊 ID бота: {self.user.id}')
        print(f'🎵 Количество серверов: {len(self.guilds)}')

async def main():
    bot = MusicBot()
    await bot.start(BOT_TOKEN)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())