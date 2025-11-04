import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from config import PLAYLISTS_DIR, ADMIN_ROLE_NAMES, BOT_OWNER_ID
from utils.audio_source import YTDLSource

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

class Playlist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_playlist_path(self, user_id, playlist_name):
        return os.path.join(PLAYLISTS_DIR, f"{user_id}_{playlist_name}.json")

    def load_playlist(self, user_id, playlist_name):
        path = self.get_playlist_path(user_id, playlist_name)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def save_playlist(self, user_id, playlist_name, songs):
        path = self.get_playlist_path(user_id, playlist_name)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(songs, f, ensure_ascii=False, indent=2)

    def get_user_playlists(self, user_id):
        playlists = []
        for filename in os.listdir(PLAYLISTS_DIR):
            if filename.startswith(f"{user_id}_"):
                playlist_name = filename.replace(f"{user_id}_", "").replace(".json", "")
                playlists.append(playlist_name)
        return playlists

    # ОБЩИЕ КОМАНДЫ
    @app_commands.command(name="playlist_create", description="Создать новый плейлист")
    @app_commands.describe(name="Название плейлиста")
    async def playlist_create(self, interaction: discord.Interaction, name: str):
        if self.load_playlist(interaction.user.id, name):
            await interaction.response.send_message(f"❌ Плейлист с названием `{name}` уже существует!")
            return
        
        self.save_playlist(interaction.user.id, name, [])
        await interaction.response.send_message(f"✅ Плейлист `{name}` создан!")

    @app_commands.command(name="playlist_add", description="Добавить песню в плейлист")
    @app_commands.describe(playlist_name="Название плейлиста", query="Название песни или ссылка")
    async def playlist_add(self, interaction: discord.Interaction, playlist_name: str, query: str):
        playlist = self.load_playlist(interaction.user.id, playlist_name)
        if playlist is None:
            await interaction.response.send_message(f"❌ Плейлист `{playlist_name}` не найден!")
            return
        
        await interaction.response.defer()
        
        if query.startswith(('http', 'www.')):
            try:
                data = await YTDLSource.get_playlist_info(query)
                if 'entries' in data:
                    songs = data['entries']
                else:
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
        playlist = self.load_playlist(interaction.user.id, playlist_name)
        if not playlist:
            await interaction.response.send_message(f"❌ Плейлист `{playlist_name}` не найден или пуст!")
            return
        
        if not interaction.user.voice:
            await interaction.response.send_message("❌ Вы должны быть в голосовом канале!", ephemeral=True)
            return
        
        music_cog = self.bot.get_cog('Music')
        if not music_cog:
            await interaction.response.send_message("❌ Модуль музыки не загружен!")
            return
        
        await interaction.response.defer()
        
        voice_channel = interaction.user.voice.channel
        guild_id = interaction.guild.id
        
        if guild_id in music_cog.voice_clients:
            voice_client = music_cog.voice_clients[guild_id]
            if voice_client.channel != voice_channel:
                await voice_client.move_to(voice_channel)
        else:
            voice_client = await voice_channel.connect()
            music_cog.voice_clients[guild_id] = voice_client
        
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

    # АДМИН КОМАНДЫ ДЛЯ УПРАВЛЕНИЯ ПЛЕЙЛИСТАМИ ПОЛЬЗОВАТЕЛЕЙ
    @app_commands.command(name="playlist_admin_remove", description="Удалить плейлист пользователя (только для админов)")
    @app_commands.describe(user_id="ID пользователя", playlist_name="Название плейлиста")
    @is_admin()
    async def playlist_admin_remove(self, interaction: discord.Interaction, user_id: str, playlist_name: str):
        try:
            user_id_int = int(user_id)
            path = self.get_playlist_path(user_id_int, playlist_name)
            
            if not os.path.exists(path):
                await interaction.response.send_message(f"❌ Плейлист `{playlist_name}` не найден у пользователя {user_id}!")
                return
            
            os.remove(path)
            await interaction.response.send_message(f"✅ Плейлист `{playlist_name}` пользователя {user_id} удален!")
        except ValueError:
            await interaction.response.send_message("❌ Неверный ID пользователя!")
        except Exception as e:
            await interaction.response.send_message(f"❌ Ошибка: {str(e)}")

    @app_commands.command(name="playlist_admin_list", description="Показать плейлисты пользователя (только для админов)")
    @app_commands.describe(user_id="ID пользователя")
    @is_admin()
    async def playlist_admin_list(self, interaction: discord.Interaction, user_id: str):
        try:
            user_id_int = int(user_id)
            playlists = []
            
            for filename in os.listdir(PLAYLISTS_DIR):
                if filename.startswith(f"{user_id_int}_"):
                    playlist_name = filename.replace(f"{user_id_int}_", "").replace(".json", "")
                    playlists.append(playlist_name)
            
            if not playlists:
                await interaction.response.send_message(f"📭 У пользователя {user_id} нет плейлистов!")
                return
            
            embed = discord.Embed(title=f"📋 Плейлисты пользователя {user_id}", color=discord.Color.purple())
            
            for playlist_name in playlists:
                playlist = self.load_playlist(user_id_int, playlist_name)
                song_count = len(playlist) if playlist else 0
                embed.add_field(
                    name=playlist_name,
                    value=f"Песен: {song_count}",
                    inline=True
                )
            
            await interaction.response.send_message(embed=embed)
        except ValueError:
            await interaction.response.send_message("❌ Неверный ID пользователя!")
        except Exception as e:
            await interaction.response.send_message(f"❌ Ошибка: {str(e)}")

async def setup(bot):
    await bot.add_cog(Playlist(bot))