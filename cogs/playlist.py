import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import shutil
from datetime import datetime
from config import PLAYLISTS_DIR, ADMIN_ROLE_NAMES, BOT_OWNER_ID, IS_RAILWAY
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
        self.backup_dir = os.path.join(PLAYLISTS_DIR, 'backups')
        os.makedirs(self.backup_dir, exist_ok=True)
        self.storage_info = self.check_storage()
        
        # Создаем бэкап только если хранилище доступно
        if self.storage_info['writable']:
            self.create_backup()
        else:
            print("⚠️ Невозможно создать бэкап: хранилище недоступно для записи")

    def check_storage(self):
        """Проверка доступного хранилища"""
        storage_info = {
            'playlists_dir': PLAYLISTS_DIR,
            'is_railway': IS_RAILWAY,
            'writable': False,
            'free_space': 'unknown'
        }
        
        try:
            # Проверяем возможность записи
            test_file = os.path.join(PLAYLISTS_DIR, "storage_test.txt")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            storage_info['writable'] = True
            
            # Проверяем свободное место (только на Railway)
            if IS_RAILWAY:
                try:
                    stat = os.statvfs(PLAYLISTS_DIR)
                    free_gb = (stat.f_bavail * stat.f_frsize) / (1024 ** 3)
                    storage_info['free_space'] = f"{free_gb:.1f} GB"
                except:
                    storage_info['free_space'] = "unknown"
            else:
                storage_info['free_space'] = "local"
                
        except Exception as e:
            print(f"⚠️ Предупреждение хранилища: {e}")
            
        return storage_info

    def create_backup(self):
        """Создание резервной копии плейлистов"""
        try:
            if not self.storage_info['writable']:
                print("❌ Невозможно создать бэкап: хранилище недоступно для записи")
                return
                
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(self.backup_dir, f'playlists_backup_{timestamp}.json')
            
            all_playlists = {}
            playlist_files = []
            
            try:
                playlist_files = [f for f in os.listdir(PLAYLISTS_DIR) if f.endswith('.json') and not f.startswith('backup')]
            except FileNotFoundError:
                print("ℹ️ Директория плейлистов пуста")
                return
            
            for filename in playlist_files:
                user_id = filename.split('_')[0]
                playlist_name = filename.replace(f"{user_id}_", "").replace(".json", "")
                filepath = os.path.join(PLAYLISTS_DIR, filename)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        all_playlists[f"{user_id}_{playlist_name}"] = json.load(f)
                except Exception as e:
                    print(f"❌ Ошибка чтения плейлиста {filename}: {e}")
            
            if all_playlists:
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(all_playlists, f, ensure_ascii=False, indent=2)
                
                print(f"✅ Создана резервная копия {len(all_playlists)} плейлистов")
                
                # Удаляем старые бэкапы (оставляем только 2 последних)
                try:
                    backups = sorted([f for f in os.listdir(self.backup_dir) if f.startswith('playlists_backup_')])
                    if len(backups) > 2:
                        for old_backup in backups[:-2]:
                            try:
                                os.remove(os.path.join(self.backup_dir, old_backup))
                                print(f"🗑️ Удален старый бэкап: {old_backup}")
                            except Exception as e:
                                print(f"❌ Ошибка удаления бэкапа {old_backup}: {e}")
                except Exception as e:
                    print(f"⚠️ Ошибка очистки старых бэкапов: {e}")
            else:
                print("ℹ️ Нет плейлистов для резервного копирования")
                
        except Exception as e:
            print(f"❌ Ошибка создания резервной копии: {e}")

    def get_playlist_path(self, user_id, playlist_name):
        return os.path.join(PLAYLISTS_DIR, f"{user_id}_{playlist_name}.json")

    def load_playlist(self, user_id, playlist_name):
        path = self.get_playlist_path(user_id, playlist_name)
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"❌ Ошибка загрузки плейлиста {path}: {e}")
                return None
        return None

    def save_playlist(self, user_id, playlist_name, songs):
        path = self.get_playlist_path(user_id, playlist_name)
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(songs, f, ensure_ascii=False, indent=2)
            print(f"✅ Плейлист сохранен: {path}")
            
            # Создаем бэкап только если хранилище доступно
            if self.storage_info['writable']:
                self.create_backup()
                
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения плейлиста {path}: {e}")
            return False

    def get_user_playlists(self, user_id):
        playlists = []
        try:
            for filename in os.listdir(PLAYLISTS_DIR):
                if filename.startswith(f"{user_id}_") and filename.endswith('.json'):
                    playlist_name = filename.replace(f"{user_id}_", "").replace(".json", "")
                    playlists.append(playlist_name)
        except Exception as e:
            print(f"❌ Ошибка получения плейлистов пользователя {user_id}: {e}")
        return playlists

    def get_all_playlists_info(self):
        playlists_info = {}
        try:
            for filename in os.listdir(PLAYLISTS_DIR):
                if filename.endswith('.json') and not filename.startswith('backup'):
                    try:
                        user_id = filename.split('_')[0]
                        playlist_name = filename.replace(f"{user_id}_", "").replace(".json", "")
                        filepath = os.path.join(PLAYLISTS_DIR, filename)
                        
                        with open(filepath, 'r', encoding='utf-8') as f:
                            songs = json.load(f)
                        
                        if user_id not in playlists_info:
                            playlists_info[user_id] = {}
                        
                        playlists_info[user_id][playlist_name] = len(songs)
                    except Exception as e:
                        print(f"❌ Ошибка чтения файла {filename}: {e}")
        except Exception as e:
            print(f"❌ Ошибка сканирования директории плейлистов: {e}")
        
        return playlists_info

    # ОБЩИЕ КОМАНДЫ ДЛЯ ВСЕХ
    @app_commands.command(name="playlist_create", description="Создать новый плейлист")
    @app_commands.describe(name="Название плейлиста")
    async def playlist_create(self, interaction: discord.Interaction, name: str):
        """Создание плейлиста - для всех"""
        if self.load_playlist(interaction.user.id, name):
            await interaction.response.send_message(f"❌ Плейлист с названием `{name}` уже существует!")
            return
        
        if self.save_playlist(interaction.user.id, name, []):
            await interaction.response.send_message(f"✅ Плейлист `{name}` создан!")
        else:
            await interaction.response.send_message("❌ Ошибка при создании плейлиста!")

    @app_commands.command(name="playlist_add", description="Добавить песню в плейлист")
    @app_commands.describe(playlist_name="Название плейлиста", query="Название песни или ссылка")
    async def playlist_add(self, interaction: discord.Interaction, playlist_name: str, query: str):
        """Добавление песни в плейлист - для всех"""
        playlist = self.load_playlist(interaction.user.id, playlist_name)
        if playlist is None:
            await interaction.response.send_message(f"❌ Плейлист `{playlist_name}` не найден!")
            return
        
        await interaction.response.defer()
        
        if query.startswith(('http', 'www.')):
            try:
                data = await YTDLSource.get_playlist_info(query)
                if data and 'entries' in data:
                    songs = data['entries']
                else:
                    songs = [data] if data else []
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
            'thumbnail': song.get('thumbnail'),
            'added_at': datetime.now().isoformat(),
            'added_by': interaction.user.id
        }
        
        playlist.append(song_info)
        if self.save_playlist(interaction.user.id, playlist_name, playlist):
            embed = discord.Embed(
                title="✅ Песня добавлена в плейлист",
                description=f"[{song_info['title']}]({song_info['url']})",
                color=discord.Color.green()
            )
            embed.add_field(name="Плейлист", value=playlist_name)
            embed.add_field(name="Всего песен", value=len(playlist))
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("❌ Ошибка при сохранении плейлиста!")

    @app_commands.command(name="playlist_play", description="Воспроизвести плейлист")
    @app_commands.describe(playlist_name="Название плейлиста")
    async def playlist_play(self, interaction: discord.Interaction, playlist_name: str):
        """Воспроизведение плейлиста - для всех"""
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
        
        # ФИКС: Добавляем await
        if not voice_client.is_playing() and queue:
            await music_cog.play_next(guild_id)
        
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
        """Список плейлистов - для всех"""
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
        """Показать плейлист - для всех"""
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
        
        # Обрезаем длинные названия
        for i, song in enumerate(playlist[:10], 1):
            title = song['title']
            if len(title) > 100:
                title = title[:97] + "..."
            duration = self.format_duration(song.get('duration'))
            embed.add_field(
                name=f"{i}. {title}",
                value=f"⏱️ {duration}",
                inline=False
            )
        
        if len(playlist) > 10:
            embed.set_footer(text=f"И еще {len(playlist) - 10} песен...")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="playlist_remove", description="Удалить песню из плейлиста")
    @app_commands.describe(playlist_name="Название плейлиста", song_number="Номер песни в плейлисте")
    async def playlist_remove(self, interaction: discord.Interaction, playlist_name: str, song_number: int):
        """Удаление песни из плейлист - для всех"""
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
        """Удаление плейлиста - для всех"""
        playlist_path = self.get_playlist_path(interaction.user.id, playlist_name)
        
        if not os.path.exists(playlist_path):
            await interaction.response.send_message(f"❌ Плейлист `{playlist_name}` не найден!")
            return
        
        try:
            os.remove(playlist_path)
            await interaction.response.send_message(f"✅ Плейлист `{playlist_name}` удален!")
        except Exception as e:
            await interaction.response.send_message(f"❌ Ошибка при удалении плейлиста: {e}")

    # АДМИН КОМАНДЫ
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

    @app_commands.command(name="storage_info", description="Информация о хранилище (только для админов)")
    @is_admin()
    async def storage_info(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="💾 Информация о хранилище",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Директория", value=self.storage_info['playlists_dir'], inline=False)
        embed.add_field(name="Railway", value="Да" if self.storage_info['is_railway'] else "Нет")
        embed.add_field(name="Доступно для записи", value="✅ Да" if self.storage_info['writable'] else "❌ Нет")
        embed.add_field(name="Свободное место", value=self.storage_info['free_space'])
        
        playlists_info = self.get_all_playlists_info()
        total_playlists = sum(len(user_playlists) for user_playlists in playlists_info.values())
        total_users = len(playlists_info)
        
        embed.add_field(name="Всего пользователей", value=total_users)
        embed.add_field(name="Всего плейлистов", value=total_playlists)
        
        backups = sorted([f for f in os.listdir(self.backup_dir) if f.startswith('playlists_backup_')])
        embed.add_field(name="Резервных копий", value=len(backups))
        
        if backups:
            latest_backup = backups[-1]
            embed.add_field(name="Последний бэкап", value=latest_backup, inline=False)
        
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
    await bot.add_cog(Playlist(bot))