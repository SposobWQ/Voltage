import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from utils.audio_source import YTDLSource
from utils.pagination import PaginationView

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_clients = {}
        self.queues = {}

    def get_queue(self, guild_id):
        if guild_id not in self.queues:
            self.queues[guild_id] = []
        return self.queues[guild_id]

    async def play_next(self, guild_id):
        queue = self.get_queue(guild_id)
        if queue and guild_id in self.voice_clients:
            voice_client = self.voice_clients[guild_id]
            if not voice_client.is_playing():
                next_song = queue.pop(0)
                voice_client.play(next_song, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(guild_id), self.bot.loop))

    class SongSelect(discord.ui.Select):
        def __init__(self, songs, music_cog):
            options = []
            for i, song in enumerate(songs[:10]):
                title = song.get('title', 'Неизвестно')[:100]
                duration = song.get('duration_string', 'Неизвестно')
                options.append(
                    discord.SelectOption(
                        label=f"{i+1}. {title}",
                        value=str(i),
                        description=f"⏱️ {duration}" if duration != 'Неизвестно' else "Длительность неизвестна"
                    )
                )
            
            super().__init__(placeholder="Выберите песню...", options=options, max_values=1)
            self.songs = songs
            self.music_cog = music_cog

        async def callback(self, interaction: discord.Interaction):
            selected_index = int(self.values[0])
            selected_song = self.songs[selected_index]
            
            await self.music_cog.play_selected_song(interaction, selected_song)

    class SongSelectView(discord.ui.View):
        def __init__(self, songs, music_cog):
            super().__init__(timeout=60)
            self.add_item(Music.SongSelect(songs, music_cog))

    async def play_selected_song(self, interaction: discord.Interaction, song):
        """Воспроизведение выбранной песни"""
        await interaction.response.defer()
        
        if not interaction.user.voice:
            await interaction.followup.send("❌ Вы должны быть в голосовом канале!", ephemeral=True)
            return
        
        voice_channel = interaction.user.voice.channel
        guild_id = interaction.guild.id
        
        # Подключение к голосовому каналу
        if guild_id in self.voice_clients:
            voice_client = self.voice_clients[guild_id]
            if voice_client.channel != voice_channel:
                await voice_client.move_to(voice_channel)
        else:
            voice_client = await voice_channel.connect()
            self.voice_clients[guild_id] = voice_client
        
        try:
            url = f"https://www.youtube.com/watch?v={song['id']}"
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            
            queue = self.get_queue(guild_id)
            
            if voice_client.is_playing() or queue:
                queue.append(player)
                embed = discord.Embed(
                    title="🎵 Добавлено в очередь",
                    description=f"[{player.title}]({url})",
                    color=discord.Color.blue()
                )
                embed.add_field(name="Позиция в очереди", value=f"#{len(queue)}")
                await interaction.followup.send(embed=embed)
            else:
                voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(guild_id), self.bot.loop))
                
                embed = discord.Embed(
                    title="🎵 Сейчас играет",
                    description=f"[{player.title}]({url})",
                    color=discord.Color.green()
                )
                embed.add_field(name="Длительность", value=song.get('duration_string', 'Неизвестно'))
                embed.add_field(name="Канал", value=voice_channel.name)
                
                await interaction.followup.send(embed=embed)
                
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка при воспроизведении: {str(e)}")

    @app_commands.command(name="play", description="Найти и воспроизвести музыку")
    @app_commands.describe(query="Название песни или ссылка")
    async def play(self, interaction: discord.Interaction, query: str):
        """Команда для воспроизведения музыки"""
        await interaction.response.defer()
        
        # Прямое воспроизведение по ссылке
        if query.startswith(('http', 'www.')):
            try:
                if not interaction.user.voice:
                    await interaction.followup.send("❌ Вы должны быть в голосовом канале!", ephemeral=True)
                    return
                
                voice_channel = interaction.user.voice.channel
                guild_id = interaction.guild.id
                
                if guild_id in self.voice_clients:
                    voice_client = self.voice_clients[guild_id]
                    if voice_client.channel != voice_channel:
                        await voice_client.move_to(voice_channel)
                else:
                    voice_client = await voice_channel.connect()
                    self.voice_clients[guild_id] = voice_client
                
                player = await YTDLSource.from_url(query, loop=self.bot.loop, stream=True)
                queue = self.get_queue(guild_id)
                
                if voice_client.is_playing() or queue:
                    queue.append(player)
                    embed = discord.Embed(
                        title="🎵 Добавлено в очередь",
                        description=f"[{player.title}]({query})",
                        color=discord.Color.blue()
                    )
                    await interaction.followup.send(embed=embed)
                else:
                    voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(guild_id), self.bot.loop))
                    embed = discord.Embed(
                        title="🎵 Сейчас играет",
                        description=f"[{player.title}]({query})",
                        color=discord.Color.green()
                    )
                    await interaction.followup.send(embed=embed)
                    
            except Exception as e:
                await interaction.followup.send(f"❌ Ошибка: {str(e)}")
            return
        
        # Поиск песен
        try:
            songs = await YTDLSource.search_songs(query, limit=10)
            
            if not songs:
                await interaction.followup.send("❌ Песни не найдены!")
                return
            
            embed = discord.Embed(
                title="🔍 Результаты поиска",
                description=f"Найдено песен по запросу: **{query}**",
                color=discord.Color.blue()
            )
            
            for i, song in enumerate(songs[:5]):
                title = song.get('title', 'Неизвестно')
                duration = song.get('duration_string', 'Неизвестно')
                embed.add_field(
                    name=f"{i+1}. {title}",
                    value=f"⏱️ {duration}",
                    inline=False
                )
            
            embed.set_footer(text="Выберите песню из списка ниже")
            
            await interaction.followup.send(embed=embed, view=self.SongSelectView(songs, self))
            
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка при поиске: {str(e)}")

    @app_commands.command(name="queue", description="Показать очередь воспроизведения")
    async def queue(self, interaction: discord.Interaction):
        """Показать текущую очередь"""
        queue = self.get_queue(interaction.guild.id)
        
        if not queue:
            await interaction.response.send_message("📭 Очередь пуста!")
            return
        
        embeds = []
        items_per_page = 5
        
        for i in range(0, len(queue), items_per_page):
            embed = discord.Embed(title="📋 Очередь воспроизведения", color=discord.Color.gold())
            page_songs = queue[i:i + items_per_page]
            
            for j, song in enumerate(page_songs, i + 1):
                embed.add_field(
                    name=f"{j}. {song.title}",
                    value=f"Длительность: {self.format_duration(song.duration)}",
                    inline=False
                )
            
            embed.set_footer(text=f"Страница {i//items_per_page + 1}/{(len(queue)-1)//items_per_page + 1}")
            embeds.append(embed)
        
        view = PaginationView(embeds) if len(embeds) > 1 else None
        await interaction.response.send_message(embed=embeds[0], view=view)

    @app_commands.command(name="skip", description="Пропустить текущий трек")
    async def skip(self, interaction: discord.Interaction):
        """Пропустить текущую песню"""
        if interaction.guild.id in self.voice_clients:
            voice_client = self.voice_clients[interaction.guild.id]
            if voice_client.is_playing():
                voice_client.stop()
                await interaction.response.send_message("⏭️ Трек пропущен")
            else:
                await interaction.response.send_message("❌ Сейчас ничего не играет")
        else:
            await interaction.response.send_message("❌ Бот не подключен к голосовому каналу")

    @app_commands.command(name="stop", description="Остановить воспроизведение и очистить очередь")
    async def stop(self, interaction: discord.Interaction):
        """Остановить музыку"""
        guild_id = interaction.guild.id
        
        if guild_id in self.voice_clients:
            voice_client = self.voice_clients[guild_id]
            voice_client.stop()
            self.queues[guild_id] = []
            await interaction.response.send_message("⏹️ Воспроизведение остановлено и очередь очищена")
        else:
            await interaction.response.send_message("❌ Бот не воспроизводит музыку")

    @app_commands.command(name="pause", description="Приостановить воспроизведение")
    async def pause(self, interaction: discord.Interaction):
        """Приостановить музыку"""
        if interaction.guild.id in self.voice_clients:
            voice_client = self.voice_clients[interaction.guild.id]
            if voice_client.is_playing():
                voice_client.pause()
                await interaction.response.send_message("⏸️ Воспроизведение приостановлено")
            else:
                await interaction.response.send_message("❌ Музыка не воспроизводится")
        else:
            await interaction.response.send_message("❌ Бот не подключен к голосовому каналу")

    @app_commands.command(name="resume", description="Возобновить воспроизведение")
    async def resume(self, interaction: discord.Interaction):
        """Возобновить музыку"""
        if interaction.guild.id in self.voice_clients:
            voice_client = self.voice_clients[interaction.guild.id]
            if voice_client.is_paused():
                voice_client.resume()
                await interaction.response.send_message("▶️ Воспроизведение возобновлено")
            else:
                await interaction.response.send_message("❌ Музыка не приостановлена")
        else:
            await interaction.response.send_message("❌ Бот не подключен к голосовому каналу")

    @app_commands.command(name="disconnect", description="Отключить бота от голосового канала")
    async def disconnect(self, interaction: discord.Interaction):
        """Отключиться от голосового канала"""
        guild_id = interaction.guild.id
        
        if guild_id in self.voice_clients:
            voice_client = self.voice_clients[guild_id]
            await voice_client.disconnect()
            del self.voice_clients[guild_id]
            if guild_id in self.queues:
                del self.queues[guild_id]
            await interaction.response.send_message("🔌 Бот отключен от голосового канала")
        else:
            await interaction.response.send_message("❌ Бот не подключен к голосовому каналу")

    def format_duration(self, seconds):
        """Форматирование длительности"""
        if not seconds:
            return "Неизвестно"
        
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"

async def setup(bot):
    await bot.add_cog(Music(bot))