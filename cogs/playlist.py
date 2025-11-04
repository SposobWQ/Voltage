import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from config import PLAYLISTS_DIR
from utils.audio_source import YTDLSource

class Playlist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_playlist_path(self, user_id, playlist_name):
        """Получить путь к файлу плейлиста"""
        return os.path.join(PLAYLISTS_DIR, f"{user_id}_{playlist_name}.json")

    def load_playlist(self, user_id, playlist_name):
        """Загрузить плейлист"""
        path = self.get_playlist_path(user_id, playlist_name)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def save_playlist(self, user_id, playlist_name, songs):
        """Сохранить плейлист"""
        path = self.get_playlist_path(user_id, playlist_name)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(songs, f, ensure_ascii=False, indent=2)

    def get_user_playlists(self, user_id):
        """Получить все плейлисты пользователя"""
        playlists = []
        for filename in os.listdir(PLAYLISTS_DIR):
            if filename.startswith(f"{user_id}_"):
                playlist_name = filename.replace(f"{user_id}_", "").replace(".json", "")
                playlists.append(playlist_name)
        return playlists

    @app_commands.command(name="playlist_create", description="Создать новый плейлист")
    @app_commands.describe(name="Название плейлиста")
    async def playlist_create(self, interaction: discord.Interaction, name: str):
        """Создать новый плейлист"""
        if self.load_playlist(interaction.user.id, name):
            await interaction.response.send_message(f"❌ Плейлист с названием `{name}` уже существует!")
            return
        
        self.save_playlist(interaction.user.id, name, [])
        await interaction.response.send_message(f"✅ Плейлист `{name}` создан!")

    @app_commands.command(name="playlist_add", description="Добавить песню в плейлист")
    @app_commands.describe(playlist_name="Название плейлиста", query="Название песни или ссылка")
    async def playlist_add(self, interaction: discord.Interaction, playlist_name: str, query: str):
        """Добавить песню в плейлист"""
        playlist = self.load_playlist(interaction.user.id, playlist_name)
        if playlist is None:
            await interaction.response.send_message(f"❌ Плейлист `{playlist_name}` не найден!")
            return
        
        await interaction.response.defer()
        
        # Поиск песни
        if query.startswith(('http', 'www.')):
            try:
                data = await YTDLSource.get_playlist_info(query)
                if 'entries' in data:
                    # Это плейлист
                    songs = data['entries']
                else:
                    # Одна песня
                    songs = [data]
            except Exception as e:
                await interaction.followup.send(f"❌ Ошибка при получении информации: {str(e)}")
                return
        else:
            songs = await YTDLSource.search_songs(query, limit=1)
        
        if not songs:
            await interaction.followup.send("❌ Песня не найдена!")
            return
        
        song = songs[0]
        song_info = {
            'id': song.get('id'),
            'title': song.get('title'),
            'url': f"https://www.youtube.com/watch?v={song.get('id')}",
            'duration': song.get('duration'),
            'thumbnail': song.get('thumbnail')
        }
        
        playlist.append(song_info)
        self.save_playlist(interaction.user.id, playlist_name, playlist)
        
        embed = discord.Embed(
            title="✅ Песня добавлена в плейлист",
            description=f"[{song_info['title']}]({song_info['url']})",
            color=discord.Color.green()
        )
        embed.add_field(name="Плейлист", value=playlist_name)
        embed.add_field(name="Всего песен", value=len(playlist))
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="playlist_play", description="Воспроизвести плейлист")
    @app_commands.describe(playlist_name="Название плейлиста")
    async def playlist_play(self, interaction: discord.Interaction, playlist_name: str):
        """Воспроизвести плейлист"""
        playlist = self.load_playlist(interaction.user.id, playlist_name)
        if not playlist:
            await interaction.response.send_message(f"❌ Плейлист `{playlist_name}` не найден или пуст!")
            return
        
        if not interaction.user.voice:
            await interaction.response.send_message("❌ Вы должны быть в голосовом канале!", ephemeral=True)
            return
        
        # Получаем ког музыки
        music_cog = self.bot.get_cog('Music')
        if not music_cog:
            await interaction.response.send_message("❌ Модуль музыки не загружен!")
            return
        
        await interaction.response.defer()
        
        voice_channel = interaction.user.voice.channel
        guild_id = interaction.guild.id
        
        # Подключаемся к каналу
        if guild_id in music_cog.voice_clients:
            voice_client = music_cog.voice_clients[guild_id]
            if voice_client.channel != voice_channel:
                await voice_client.move_to(voice_channel)
        else:
            voice_client = await voice_channel.connect()
            music_cog.voice_clients[guild_id] = voice_client
        
        # Добавляем песни в очередь
        queue = music_cog.get_queue(guild_id)
        added_count = 0
        
        for song_info in playlist:
            try:
                player = await YTDLSource.from_url(song_info['url'], loop=self.bot.loop, stream=True)
                queue.append(player)
                added_count += 1
            except Exception as e:
                print(f"Ошибка при добавлении песни {song_info['title']}: {e}")
                continue
        
        # Если ничего не играет, начинаем воспроизведение
        if not voice_client.is_playing() and queue:
            music_cog.play_next(guild_id)
        
        embed = discord.Embed(
            title="🎵 Плейлист добавлен в очередь",
            description=f"Плейлист: **{playlist_name}**",
            color=discord.Color.blue()
        )
        embed.add_field(name="Добавлено песен", value=added_count)
        embed.add_field(name="Всего в очереди", value=len(queue))
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="playlist_list", description="Показать мои плейлисты")
    async def playlist_list(self, interaction: discord.Interaction):
        """Показать все плейлисты пользователя"""
        playlists = self.get_user_playlists(interaction.user.id)
        
        if not playlists:
            await interaction.response.send_message("📭 У вас нет плейлистов!")
            return
        
        embed = discord.Embed(title="📋 Ваши плейлисты", color=discord.Color.purple())
        
        for playlist_name in playlists:
            playlist = self.load_playlist(interaction.user.id, playlist_name)
            song_count = len(playlist) if playlist else 0
            embed.add_field(
                name=playlist_name,
                value=f"Песен: {song_count}",
                inline=True
            )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="playlist_show", description="Показать содержимое плейлиста")
    @app_commands.describe(playlist_name="Название плейлиста")
    async def playlist_show(self, interaction: discord.Interaction, playlist_name: str):
        """Показать содержимое плейлиста"""
        playlist = self.load_playlist(interaction.user.id, playlist_name)
        
        if not playlist:
            await interaction.response.send_message(f"❌ Плейлист `{playlist_name}` не найден!")
            return
        
        if not playlist:
            await interaction.response.send_message(f"📭 Плейлист `{playlist_name}` пуст!")
            return
        
        embed = discord.Embed(
            title=f"📋 Плейлист: {playlist_name}",
            description=f"Всего песен: {len(playlist)}",
            color=discord.Color.blue()
        )
        
        for i, song in enumerate(playlist[:10], 1):  # Показываем первые 10 песен
            duration = self.format_duration(song.get('duration'))
            embed.add_field(
                name=f"{i}. {song['title']}",
                value=f"⏱️ {duration}",
                inline=False
            )
        
        if len(playlist) > 10:
            embed.set_footer(text=f"И еще {len(playlist) - 10} песен...")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="playlist_remove", description="Удалить песню из плейлиста")
    @app_commands.describe(playlist_name="Название плейлиста", song_number="Номер песни в плейлисте")
    async def playlist_remove(self, interaction: discord.Interaction, playlist_name: str, song_number: int):
        """Удалить песню из плейлиста"""
        playlist = self.load_playlist(interaction.user.id, playlist_name)
        
        if not playlist:
            await interaction.response.send_message(f"❌ Плейлист `{playlist_name}` не найден!")
            return
        
        if song_number < 1 or song_number > len(playlist):
            await interaction.response.send_message(f"❌ Неверный номер песни! Должен быть от 1 до {len(playlist)}")
            return
        
        removed_song = playlist.pop(song_number - 1)
        self.save_playlist(interaction.user.id, playlist_name, playlist)
        
        embed = discord.Embed(
            title="✅ Песня удалена из плейлиста",
            description=f"[{removed_song['title']}]({removed_song['url']})",
            color=discord.Color.green()
        )
        embed.add_field(name="Плейлист", value=playlist_name)
        embed.add_field(name="Осталось песен", value=len(playlist))
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="playlist_delete", description="Удалить плейлист")
    @app_commands.describe(playlist_name="Название плейлиста")
    async def playlist_delete(self, interaction: discord.Interaction, playlist_name: str):
        """Удалить плейлист"""
        path = self.get_playlist_path(interaction.user.id, playlist_name)
        
        if not os.path.exists(path):
            await interaction.response.send_message(f"❌ Плейлист `{playlist_name}` не найден!")
            return
        
        os.remove(path)
        await interaction.response.send_message(f"✅ Плейлист `{playlist_name}` удален!")

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
    await bot.add_cog(Playlist(bot))