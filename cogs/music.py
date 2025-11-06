import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from utils.audio_source import YTDLSource
from utils.pagination import PaginationView
from config import ADMIN_ROLE_NAMES, BOT_OWNER_ID, FFMPEG_OPTIONS

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
        self.volume_settings = {}  # Храним громкость для каждого сервера

    def get_queue(self, guild_id):
        if guild_id not in self.queues:
            self.queues[guild_id] = []
        return self.queues[guild_id]

    def get_quality_setting(self, guild_id):
        if guild_id not in self.quality_settings:
            self.quality_settings[guild_id] = 'high'  # По умолчанию высокое качество
        return self.quality_settings[guild_id]

    def get_volume_setting(self, guild_id):
        if guild_id not in self.volume_settings:
            self.volume_settings[guild_id] = 0.5  # По умолчанию 50% громкость
        return self.volume_settings[guild_id]

    def update_all_volumes(self, guild_id, volume_level):
        """Обновляет громкость для всех треков в очереди и текущего"""
        self.volume_settings[guild_id] = volume_level
        
        # Обновляем громкость текущего трека
        if guild_id in self.voice_clients:
            voice_client = self.voice_clients[guild_id]
            if voice_client.source:
                voice_client.source.volume = volume_level
        
        # Обновляем громкость треков в очереди
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
                
                # Устанавливаем громкость для следующего трека
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
                # ФИКС: Обрезаем название для Discord (максимум 100 символов)
                if len(title) > 90:
                    title = title[:87] + "..."
                
                duration = song.get('duration_string', 'Неизвестно')
                description = f"⏱️ {duration}" if duration != 'Неизвестно' else "Длительность неизвестна"
                # ФИКС: Обрезаем описание (максимум 50 символов)
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
            
            # Устанавливаем громкость для нового трека
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
            if "возрастное ограничение" in error_msg.lower() or "age" in error_msg.lower() or "inappropriate" in error_msg.lower():
                embed = discord.Embed(
                    title="🔞 Возрастное ограничение",
                    description="Это видео имеет возрастное ограничение и не может быть воспроизведено.",
                    color=discord.Color.red()
                )
                embed.add_field(name="Решение", value="Попробуйте другую песню")
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send(f"❌ Ошибка при воспроизведении: {error_msg}")

    # ОБЩИЕ КОМАНДЫ (ДЛЯ ВСЕХ)
    @app_commands.command(name="play", description="Найти и воспроизвести музыку")
    @app_commands.describe(query="Название песни или ссылка")
    async def play(self, interaction: discord.Interaction, query: str):
        """Воспроизведение музыки - для всех"""
        await interaction.response.defer()
        
        # Проверяем, находится ли пользователь в голосовом канале
        if not interaction.user.voice:
            await interaction.followup.send("❌ Вы должны быть в голосовом канале!", ephemeral=True)
            return
        
        # Если это прямая ссылка
        if query.startswith(('http', 'www.')):
            try:
                voice_channel = interaction.user.voice.channel
                guild_id = interaction.guild.id
                
                # Подключаемся к голосовому каналу
                if guild_id in self.voice_clients:
                    voice_client = self.voice_clients[guild_id]
                    if voice_client.channel != voice_channel:
                        await voice_client.move_to(voice_channel)
                else:
                    voice_client = await voice_channel.connect()
                    self.voice_clients[guild_id] = voice_client
                
                # Загружаем и воспроизводим трек
                player = await YTDLSource.from_url(query, loop=self.bot.loop, stream=True)
                
                # Устанавливаем громкость
                volume = self.get_volume_setting(guild_id)
                player.volume = volume
                
                queue = self.get_queue(guild_id)
                
                # Если что-то уже играет или есть очередь, добавляем в очередь
                if voice_client.is_playing() or queue:
                    queue.append(player)
                    embed = discord.Embed(
                        title="🎵 Добавлено в очередь",
                        description=f"[{player.title}]({query})",
                        color=discord.Color.blue()
                    )
                    embed.add_field(name="Громкость", value=f"{int(volume * 100)}%")
                    embed.add_field(name="Качество", value=self.get_quality_setting(guild_id))
                    embed.add_field(name="Позиция в очереди", value=f"#{len(queue)}")
                    await interaction.followup.send(embed=embed)
                else:
                    # Если ничего не играет, начинаем воспроизведение
                    voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(guild_id), self.bot.loop))
                    embed = discord.Embed(
                        title="🎵 Сейчас играет",
                        description=f"[{player.title}]({query})",
                        color=discord.Color.green()
                    )
                    embed.add_field(name="Громкость", value=f"{int(volume * 100)}%")
                    embed.add_field(name="Качество", value=self.get_quality_setting(guild_id))
                    await interaction.followup.send(embed=embed)
                    
            except Exception as e:
                error_msg = str(e)
                if "возрастное ограничение" in error_msg.lower() or "age" in error_msg.lower() or "inappropriate" in error_msg.lower():
                    embed = discord.Embed(
                        title="🔞 Возрастное ограничение",
                        description="Это видео имеет возрастное ограничение и не может быть воспроизведено.",
                        color=discord.Color.red()
                    )
                    embed.add_field(name="Решение", value="Попробуйте другую песню")
                    await interaction.followup.send(embed=embed)
                else:
                    await interaction.followup.send(f"❌ Ошибка: {error_msg}")
            return
        
        # Поиск песен по запросу
        try:
            songs = await YTDLSource.search_songs(query, limit=10)
            
            if not songs:
                await interaction.followup.send("❌ Песни не найдены!")
                return
            
            # Показываем результаты поиска
            volume = self.get_volume_setting(interaction.guild.id)
            quality = self.get_quality_setting(interaction.guild.id)
            
            embed = discord.Embed(
                title="🔍 Результаты поиска",
                description=f"Найдено песен по запросу: **{query}**",
                color=discord.Color.blue()
            )
            
            # Показываем текущие настройки
            embed.add_field(name="Текущая громкость", value=f"{int(volume * 100)}%", inline=True)
            embed.add_field(name="Текущее качество", value=quality, inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=True)  # Пустое поле для выравнивания
            
            # ФИКС: Обрезаем названия для embed полей
            for i, song in enumerate(songs[:5]):
                title = song.get('title', 'Неизвестно')
                if len(title) > 200:
                    title = title[:197] + "..."
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

    @app_commands.command(name="stop", description="Остановить воспроизведение")
    async def stop(self, interaction: discord.Interaction):
        """Остановка музыки - для всех"""
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
        """Пропуск трека - для всех"""
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
        """Показать очередь - для всех"""
        queue = self.get_queue(interaction.guild.id)
        
        if not queue:
            await interaction.response.send_message("📭 Очередь пуста!")
            return
        
        volume = self.get_volume_setting(interaction.guild.id)
        quality = self.get_quality_setting(interaction.guild.id)
        
        embed = discord.Embed(
            title="📋 Очередь воспроизведения", 
            color=discord.Color.gold()
        )
        embed.add_field(name="🔊 Громкость", value=f"{int(volume * 100)}%", inline=True)
        embed.add_field(name="🎚️ Качество", value=quality, inline=True)
        embed.add_field(name="🎵 Треков в очереди", value=len(queue), inline=True)
        
        # ФИКС: Обрезаем названия в очереди
        for i, song in enumerate(queue[:8], 1):
            title = song.title
            if len(title) > 100:
                title = title[:97] + "..."
            embed.add_field(
                name=f"{i}. {title}",
                value=f"⏱️ Длительность: {self.format_duration(song.duration)}",
                inline=False
            )
        
        if len(queue) > 8:
            embed.set_footer(text=f"И еще {len(queue) - 8} песен...")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="now_playing", description="Показать текущий трек")
    async def now_playing(self, interaction: discord.Interaction):
        """Текущий трек - для всех"""
        guild_id = interaction.guild.id
        
        if guild_id in self.voice_clients:
            voice_client = self.voice_clients[guild_id]
            if voice_client.is_playing() and hasattr(voice_client.source, 'title'):
                current_song = voice_client.source
                volume = self.get_volume_setting(guild_id)
                quality = self.get_quality_setting(guild_id)
                
                embed = discord.Embed(
                    title="🎵 Сейчас играет",
                    description=f"**{current_song.title}**",
                    color=discord.Color.green()
                )
                if hasattr(current_song, 'url'):
                    embed.description = f"[{current_song.title}]({current_song.url})"
                if hasattr(current_song, 'duration'):
                    embed.add_field(name="⏱️ Длительность", value=self.format_duration(current_song.duration))
                
                embed.add_field(name="🔊 Громкость", value=f"{int(volume * 100)}%")
                embed.add_field(name="🎚️ Качество", value=quality)
                
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message("❌ Сейчас ничего не играет")
        else:
            await interaction.response.send_message("❌ Бот не подключен к голосовому каналу")

    @app_commands.command(name="pause", description="Приостановить воспроизведение")
    async def pause(self, interaction: discord.Interaction):
        """Пауза - для всех"""
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
        """Продолжить - для всех"""
        if interaction.guild.id in self.voice_clients:
            voice_client = self.voice_clients[interaction.guild.id]
            if voice_client.is_paused():
                voice_client.resume()
                await interaction.response.send_message("▶️ Воспроизведение возобновлено")
            else:
                await interaction.response.send_message("❌ Музыка не приостановлена")
        else:
            await interaction.response.send_message("❌ Бот не подключен к голосовому каналу")

    @app_commands.command(name="current_settings", description="Показать текущие настройки")
    async def current_settings(self, interaction: discord.Interaction):
        """Показать текущие настройки - для всех"""
        guild_id = interaction.guild.id
        volume = self.get_volume_setting(guild_id)
        quality = self.get_quality_setting(guild_id)
        
        embed = discord.Embed(
            title="⚙️ Текущие настройки",
            color=discord.Color.purple()
        )
        embed.add_field(name="🔊 Громкость", value=f"{int(volume * 100)}%", inline=True)
        embed.add_field(name="🎚️ Качество", value=quality, inline=True)
        
        # Информация о очереди
        queue = self.get_queue(guild_id)
        embed.add_field(name="📋 Треков в очереди", value=len(queue), inline=True)
        
        # Информация о подключении
        if guild_id in self.voice_clients:
            voice_client = self.voice_clients[guild_id]
            embed.add_field(name="🔗 Подключен к", value=voice_client.channel.name, inline=True)
            status = "▶️ Играет" if voice_client.is_playing() else "⏸️ На паузе" if voice_client.is_paused() else "⏹️ Остановлено"
            embed.add_field(name="📊 Статус", value=status, inline=True)
        else:
            embed.add_field(name="🔗 Подключение", value="❌ Не подключен", inline=True)
        
        await interaction.response.send_message(embed=embed)

    # АДМИН КОМАНДЫ
    @app_commands.command(name="volume", description="Изменить громкость (только для админов)")
    @app_commands.describe(level="Уровень громкости (1-100)")
    @is_admin()
    async def volume(self, interaction: discord.Interaction, level: int):
        """Изменение громкости - для админов"""
        if level < 1 or level > 100:
            await interaction.response.send_message("❌ Громкость должна быть от 1 до 100!", ephemeral=True)
            return
        
        guild_id = interaction.guild.id
        volume_level = level / 100
        
        # Обновляем громкость для всех треков
        self.update_all_volumes(guild_id, volume_level)
        
        embed = discord.Embed(
            title="🔊 Громкость изменена",
            description=f"Установлена громкость: **{level}%**",
            color=discord.Color.green()
        )
        embed.add_field(name="Применено к", value="Текущему треку и всей очереди")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="disconnect", description="Отключить бота от голосового канала (только для админов)")
    @is_admin()
    async def disconnect(self, interaction: discord.Interaction):
        """Отключение бота - для админов"""
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

    @app_commands.command(name="clear_queue", description="Очистить очередь (только для админов)")
    @is_admin()
    async def clear_queue(self, interaction: discord.Interaction):
        """Очистка очереди - для админов"""
        guild_id = interaction.guild.id
        queue_count = len(self.get_queue(guild_id))
        self.queues[guild_id] = []
        
        embed = discord.Embed(
            title="🗑️ Очередь очищена",
            description=f"Удалено {queue_count} треков из очереди",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="quality", description="Изменить качество звука (только для админов)")
    @app_commands.describe(quality="Качество: low, medium, high")
    @is_admin()
    async def quality(self, interaction: discord.Interaction, quality: str):
        """Изменение качества звука - для админов"""
        quality = quality.lower()
        if quality not in ['low', 'medium', 'high']:
            await interaction.response.send_message("❌ Доступные качества: low, medium, high", ephemeral=True)
            return
        
        guild_id = interaction.guild.id
        self.quality_settings[guild_id] = quality
        
        quality_descriptions = {
            'low': '📉 Низкое (64kbps) - экономит трафик',
            'medium': '⚖️ Среднее (128kbps) - баланс качества',
            'high': '📈 Высокое (192kbps) - лучшее качество'
        }
        
        embed = discord.Embed(
            title="🎚️ Качество звука изменено",
            description=f"Установлено качество: **{quality}**",
            color=discord.Color.blue()
        )
        embed.add_field(name="Описание", value=quality_descriptions[quality])
        embed.add_field(name="Применяется к", value="Следующим трекам")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="eq", description="Настройка эквалайзера (только для админов)")
    @app_commands.describe(preset="Пресет: default, bass, treble, flat, rock, clear")
    @is_admin()
    async def eq(self, interaction: discord.Interaction, preset: str):
        """Настройка эквалайзера - для админов"""
        eq_presets = {
            'default': '-af "volume=1.0"',
            'bass': '-af "bass=g=8, volume=0.9"',
            'treble': '-af "treble=g=5, volume=1.0"',
            'flat': '-af "volume=1.0"',
            'rock': '-af "equalizer=f=100:width_type=o:width=1:g=5, equalizer=f=1000:width_type=o:width=2:g=2, equalizer=f=4000:width_type=o:width=3:g=3"',
            'clear': '-af "volume=1.1, highpass=f=300, lowpass=f=8000"'
        }
        
        if preset.lower() in eq_presets:
            embed = discord.Embed(
                title="🎛️ Эквалайзер",
                description=f"Пресет установлен: **{preset}**",
                color=discord.Color.blue()
            )
            embed.add_field(name="Эффект", value=eq_presets[preset.lower()])
            await interaction.response.send_message(embed=embed)
        else:
            available_presets = ", ".join(eq_presets.keys())
            await interaction.response.send_message(f"❌ Доступные пресеты: {available_presets}", ephemeral=True)

    @app_commands.command(name="volume_boost", description="Усиление громкости (только для админов)")
    @app_commands.describe(boost="Усиление (1.0 = нормально, 2.0 = в 2 раза громче)")
    @is_admin()
    async def volume_boost(self, interaction: discord.Interaction, boost: float):
        """Усиление громкости - для админов"""
        if boost < 0.5 or boost > 3.0:
            await interaction.response.send_message("❌ Усиление должно быть от 0.5 до 3.0!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🔊 Усиление громкости",
            description=f"Установлено усиление: **{boost}x**",
            color=discord.Color.green()
        )
        embed.add_field(name="Эффект", value=f"Звук будет в {boost} раз громче")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="cookies_status", description="Проверить статус cookies")
    async def cookies_status(self, interaction: discord.Interaction):
        """Проверка статуса cookies"""
        import os
        import json
        
        try:
            if os.path.exists('cookies.txt'):
                with open('cookies.txt', 'r') as f:
                    content = f.read()
                
                # Считаем количество куки
                lines = content.split('\n')
                cookie_count = sum(1 for line in lines if line and not line.startswith('#') and '\t' in line)
                
                embed = discord.Embed(
                    title="🔑 Статус Cookies",
                    description=f"Загружено **{cookie_count}** cookies",
                    color=discord.Color.green()
                )
                
                # Проверяем важные куки
                important_cookies = ['__Secure-3PSID', '__Secure-3PAPISID', 'LOGIN_INFO']
                found = []
                for line in lines:
                    for important in important_cookies:
                        if important in line and not line.startswith('#'):
                            found.append(important)
                            break
                
                if found:
                    embed.add_field(name="✅ Важные cookies", value=", ".join(set(found)), inline=False)
                else:
                    embed.add_field(name="⚠️ Внимание", value="Важные cookies не найдены", inline=False)
                    
            else:
                embed = discord.Embed(
                    title="🔑 Статус Cookies",
                    description="Файл cookies не найден",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="💡 Решение", 
                    value="Файл cookies.txt должен быть в папке с ботом",
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Ошибка: {str(e)}", ephemeral=True)

    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    def format_duration(self, seconds):
        """Форматирование длительности в читаемый вид"""
        if not seconds:
            return "Неизвестно"
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"

    def create_progress_bar(self, progress, length=20):
        """Создание прогресс-бара"""
        filled = int(length * progress)
        empty = length - filled
        return f"█" * filled + "░" * empty + f" {progress:.1%}"

    # ОБРАБОТЧИКИ СОБЫТИЙ
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Автоматическое отключение бота если все вышли из канала"""
        if member.bot:
            return
        
        # Проверяем все голосовые клиенты
        for guild_id, voice_client in list(self.voice_clients.items()):
            if voice_client.channel:
                # Если в канале остался только бот
                if len(voice_client.channel.members) == 1 and voice_client.channel.members[0].bot:
                    await asyncio.sleep(60)  # Ждем 60 секунд
                    
                    # Проверяем еще раз
                    if (voice_client.channel and 
                        len(voice_client.channel.members) == 1 and 
                        voice_client.channel.members[0].bot):
                        
                        await voice_client.disconnect()
                        del self.voice_clients[guild_id]
                        if guild_id in self.queues:
                            del self.queues[guild_id]
                        print(f"🔌 Бот автоматически отключен от {voice_client.channel.name}")

async def setup(bot):
    await bot.add_cog(Music(bot))