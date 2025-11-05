import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from utils.audio_source import YTDLSource
from utils.pagination import PaginationView
from config import ADMIN_ROLE_NAMES, BOT_OWNER_ID, FFMPEG_OPTIONS
from cogs.playlist import Playlist

def is_admin():
    async def predicate(interaction: discord.Interaction):
        if interaction.user.id == BOT_OWNER_ID:
            return True
        if interaction.user.guild_permissions.administrator:
            return True
        user_roles = [role.name for role in interaction.user.roles]
        if any(role_name in ADMIN_ROLE_NAMES for role_name in user_roles):
            return True
        await interaction.response.send_message("❌ У вас нет прав для использования этой команды!", ephemeral=True)
        return False
    return app_commands.check(predicate)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_clients = {}
        self.queues = {}
        self.quality_settings = {}
        self.volume_settings = {}

    def get_queue(self, guild_id):
        if guild_id not in self.queues:
            self.queues[guild_id] = []
        return self.queues[guild_id]

    def get_quality_setting(self, guild_id):
        if guild_id not in self.quality_settings:
            self.quality_settings[guild_id] = 'high'
        return self.quality_settings[guild_id]

    def get_volume_setting(self, guild_id):
        if guild_id not in self.volume_settings:
            self.volume_settings[guild_id] = 0.5
        return self.volume_settings[guild_id]

    def update_all_volumes(self, guild_id, volume_level):
        self.volume_settings[guild_id] = volume_level
        
        if guild_id in self.voice_clients:
            voice_client = self.voice_clients[guild_id]
            if voice_client.source:
                voice_client.source.volume = volume_level
        
        queue = self.get_queue(guild_id)
        for song in queue:
            if hasattr(song, 'volume'):
                song.volume = volume_level

    async def play_next(self, guild_id):
        queue = self.get_queue(guild_id)
        if queue and guild_id in self.voice_clients:
            voice_client = self.voice_clients[guild_id]
            if not voice_client.is_playing():
                next_song = queue.pop(0)
                
                volume = self.get_volume_setting(guild_id)
                if hasattr(next_song, 'volume'):
                    next_song.volume = volume
                
                await asyncio.sleep(0.1)
                
                def after_play(error):
                    if error:
                        print(f'Ошибка воспроизведения: {error}')
                    asyncio.run_coroutine_threadsafe(self.play_next(guild_id), self.bot.loop)
                
                voice_client.play(next_song, after=after_play)

    class SongSelect(discord.ui.Select):
        def __init__(self, songs, music_cog):
            options = []
            for i, song in enumerate(songs[:10]):
                title = song.get('title', 'Неизвестно')
                # ФИКС: Обрезаем название для Discord
                if len(title) > 90:
                    title = title[:87] + "..."
                
                duration = song.get('duration_string', 'Неизвестно')
                description = f"⏱️ {duration}" if duration != 'Неизвестно' else "Длительность неизвестна"
                # ФИКС: Обрезаем описание
                if len(description) > 45:
                    description = description[:42] + "..."
                
                options.append(
                    discord.SelectOption(
                        label=f"{i+1}. {title}",
                        value=str(i),
                        description=description
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
        await interaction.response.defer()
        
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
        
        try:
            url = f"https://www.youtube.com/watch?v={song['id']}"
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            
            volume = self.get_volume_setting(guild_id)
            player.volume = volume
            
            queue = self.get_queue(guild_id)
            
            if voice_client.is_playing() or queue:
                queue.append(player)
                embed = discord.Embed(
                    title="🎵 Добавлено в очередь",
                    description=f"[{player.title}]({url})",
                    color=discord.Color.blue()
                )
                embed.add_field(name="Позиция в очереди", value=f"#{len(queue)}")
                embed.add_field(name="Громкость", value=f"{int(volume * 100)}%")
                embed.add_field(name="Качество", value=self.get_quality_setting(guild_id))
                await interaction.followup.send(embed=embed)
            else:
                voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(guild_id), self.bot.loop))
                
                embed = discord.Embed(
                    title="🎵 Сейчас играет",
                    description=f"[{player.title}]({url})",
                    color=discord.Color.green()
                )
                embed.add_field(name="Длительность", value=song.get('duration_string', 'Неизвестно'))
                embed.add_field(name="Громкость", value=f"{int(volume * 100)}%")
                embed.add_field(name="Качество", value=self.get_quality_setting(guild_id))
                
                await interaction.followup.send(embed=embed)
                
        except Exception as e:
            error_msg = str(e)
            if "возрастное ограничение" in error_msg.lower() or "age" in error_msg.lower():
                embed = discord.Embed(
                    title="🔞 Возрастное ограничение",
                    description="Это видео имеет возрастное ограничение и не может быть воспроизведено.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send(f"❌ Ошибка: {error_msg}")

    # КОМАНДЫ
    @app_commands.command(name="play", description="Найти и воспроизвести музыку")
    @app_commands.describe(query="Название песни или ссылка")
    async def play(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        
        if not interaction.user.voice:
            await interaction.followup.send("❌ Вы должны быть в голосовом канале!", ephemeral=True)
            return
        
        if query.startswith(('http', 'www.')):
            try:
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
                
                volume = self.get_volume_setting(guild_id)
                player.volume = volume
                
                queue = self.get_queue(guild_id)
                
                if voice_client.is_playing() or queue:
                    queue.append(player)
                    embed = discord.Embed(
                        title="🎵 Добавлено в очередь",
                        description=f"[{player.title}]({query})",
                        color=discord.Color.blue()
                    )
                    embed.add_field(name="Громкость", value=f"{int(volume * 100)}%")
                    embed.add_field(name="Позиция в очереди", value=f"#{len(queue)}")
                    await interaction.followup.send(embed=embed)
                else:
                    voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(guild_id), self.bot.loop))
                    embed = discord.Embed(
                        title="🎵 Сейчас играет",
                        description=f"[{player.title}]({query})",
                        color=discord.Color.green()
                    )
                    embed.add_field(name="Громкость", value=f"{int(volume * 100)}%")
                    await interaction.followup.send(embed=embed)
                    
            except Exception as e:
                error_msg = str(e)
                if "возрастное ограничение" in error_msg.lower():
                    embed = discord.Embed(
                        title="🔞 Возрастное ограничение",
                        description="Это видео имеет возрастное ограничение.",
                        color=discord.Color.red()
                    )
                    await interaction.followup.send(embed=embed)
                else:
                    await interaction.followup.send(f"❌ Ошибка: {error_msg}")
            return
        
        try:
            songs = await YTDLSource.search_songs(query, limit=10)
            
            if not songs:
                await interaction.followup.send("❌ Песни не найдены!")
                return
            
            volume = self.get_volume_setting(interaction.guild.id)
            quality = self.get_quality_setting(interaction.guild.id)
            
            embed = discord.Embed(
                title="🔍 Результаты поиска",
                description=f"Найдено песен по запросу: **{query}**",
                color=discord.Color.blue()
            )
            
            embed.add_field(name="Текущая громкость", value=f"{int(volume * 100)}%", inline=True)
            embed.add_field(name="Текущее качество", value=quality, inline=True)
            
            # ФИКС: Обрезаем названия в embed
            for i, song in enumerate(songs[:5]):
                title = song.get('title', 'Неизвестно')
                if len(title) > 256:  # Discord embed field value limit
                    title = title[:253] + "..."
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

    # Остальные команды остаются без изменений...
    @app_commands.command(name="stop", description="Остановить воспроизведение")
    async def stop(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        
        if guild_id in self.voice_clients:
            voice_client = self.voice_clients[guild_id]
            voice_client.stop()
            self.queues[guild_id] = []
            await interaction.response.send_message("⏹️ Воспроизведение остановлено и очередь очищена")
        else:
            await interaction.response.send_message("❌ Бот не воспроизводит музыку")

    @app_commands.command(name="skip", description="Пропустить текущий трек")
    async def skip(self, interaction: discord.Interaction):
        if interaction.guild.id in self.voice_clients:
            voice_client = self.voice_clients[interaction.guild.id]
            if voice_client.is_playing():
                voice_client.stop()
                await interaction.response.send_message("⏭️ Трек пропущен")
            else:
                await interaction.response.send_message("❌ Сейчас ничего не играет")
        else:
            await interaction.response.send_message("❌ Бот не подключен к голосовому каналу")

    @app_commands.command(name="queue", description="Показать очередь воспроизведения")
    async def queue(self, interaction: discord.Interaction):
        queue = self.get_queue(interaction.guild.id)
        
        if not queue:
            await interaction.response.send_message("📭 Очередь пуста!")
            return
        
        volume = self.get_volume_setting(interaction.guild.id)
        quality = self.get_quality_setting(interaction.guild.id)
        
        embed = discord.Embed(title="📋 Очередь воспроизведения", color=discord.Color.gold())
        embed.add_field(name="🔊 Громкость", value=f"{int(volume * 100)}%", inline=True)
        embed.add_field(name="🎚️ Качество", value=quality, inline=True)
        embed.add_field(name="🎵 Треков в очереди", value=len(queue), inline=True)
        
        for i, song in enumerate(queue[:8], 1):
            title = song.title
            if len(title) > 100:
                title = title[:97] + "..."
            embed.add_field(
                name=f"{i}. {title}",
                value=f"⏱️ {self.format_duration(song.duration)}",
                inline=False
            )
        
        if len(queue) > 8:
            embed.set_footer(text=f"И еще {len(queue) - 8} песен...")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="volume", description="Изменить громкость (только для админов)")
    @app_commands.describe(level="Уровень громкости (1-100)")
    @is_admin()
    async def volume(self, interaction: discord.Interaction, level: int):
        if level < 1 or level > 100:
            await interaction.response.send_message("❌ Громкость должна быть от 1 до 100!", ephemeral=True)
            return
        
        guild_id = interaction.guild.id
        volume_level = level / 100
        
        self.update_all_volumes(guild_id, volume_level)
        
        embed = discord.Embed(
            title="🔊 Громкость изменена",
            description=f"Установлена громкость: **{level}%**",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    def format_duration(self, seconds):
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