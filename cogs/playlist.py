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
        self.create_backup()

    def create_backup(self):
        """Создание резервной копии плейлистов"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(self.backup_dir, f'playlists_backup_{timestamp}.json')
            
            all_playlists = {}
            for filename in os.listdir(PLAYLISTS_DIR):
                if filename.endswith('.json') and not filename.startswith('backup'):
                    user_id = filename.split('_')[0]
                    playlist_name = filename.replace(f"{user_id}_", "").replace(".json", "")
                    filepath = os.path.join(PLAYLISTS_DIR, filename)
                    
                    with open(filepath, 'r', encoding='utf-8') as f:
                        all_playlists[f"{user_id}_{playlist_name}"] = json.load(f)
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(all_playlists, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Создана резервная копия плейлистов: {backup_file}")
            
            # Удаляем старые бэкапы (оставляем последние 5)
            backups = sorted([f for f in os.listdir(self.backup_dir) if f.startswith('playlists_backup_')])
            if len(backups) > 5:
                for old_backup in backups[:-5]:
                    os.remove(os.path.join(self.backup_dir, old_backup))
                    
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
            
            # Создаем бэкап после значимых изменений
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
        """Получить информацию о всех плейлистах"""
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

    # ОБЩИЕ КОМАНДЫ
    @app_commands.command(name="playlist_create", description="Создать новый плейлист")
    @app_commands.describe(name="Название плейлиста")
    async def playlist_create(self, interaction: discord.Interaction, name: str):
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

    # ... остальные команды из предыдущей версии ...

    # НОВЫЕ АДМИН КОМАНДЫ ДЛЯ УПРАВЛЕНИЯ ДАННЫМИ
    @app_commands.command(name="playlist_backup", description="Создать резервную копию всех плейлистов (только для админов)")
    @is_admin()
    async def playlist_backup(self, interaction: discord.Interaction):
        """Создание резервной копии"""
        await interaction.response.defer()
        
        try:
            self.create_backup()
            
            # Получаем информацию о бэкапах
            backups = sorted([f for f in os.listdir(self.backup_dir) if f.startswith('playlists_backup_')])
            latest_backup = backups[-1] if backups else "нет"
            
            embed = discord.Embed(
                title="📦 Резервное копирование",
                description="Резервная копия плейлистов создана!",
                color=discord.Color.green()
            )
            embed.add_field(name="Последний бэкап", value=latest_backup)
            embed.add_field(name="Всего бэкапов", value=len(backups))
            embed.add_field(name="Директория", value=self.backup_dir, inline=False)
            
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка создания резервной копии: {str(e)}")

    @app_commands.command(name="playlist_stats", description="Статистика плейлистов (только для админов)")
    @is_admin()
    async def playlist_stats(self, interaction: discord.Interaction):
        """Статистика по плейлистам"""
        await interaction.response.defer()
        
        try:
            playlists_info = self.get_all_playlists_info()
            total_playlists = sum(len(user_playlists) for user_playlists in playlists_info.values())
            total_users = len(playlists_info)
            total_songs = sum(sum(playlist_info.values()) for playlist_info in playlists_info.values())
            
            embed = discord.Embed(
                title="📊 Статистика плейлистов",
                color=discord.Color.blue()
            )
            embed.add_field(name="Всего пользователей", value=total_users)
            embed.add_field(name="Всего плейлистов", value=total_playlists)
            embed.add_field(name="Всего песен", value=total_songs)
            embed.add_field(name="Директория", value=PLAYLISTS_DIR, inline=False)
            embed.add_field(name="Режим Railway", value=IS_RAILWAY, inline=False)
            
            # Топ пользователей по количеству плейлистов
            top_users = sorted(
                [(user_id, len(playlists)) for user_id, playlists in playlists_info.items()],
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            if top_users:
                top_text = "\n".join([f"<@{user_id}>: {count} плейлистов" for user_id, count in top_users])
                embed.add_field(name="Топ пользователей", value=top_text, inline=False)
            
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка получения статистики: {str(e)}")

    @app_commands.command(name="playlist_export", description="Экспортировать плейлист в файл (только для админов)")
    @app_commands.describe(user_id="ID пользователя", playlist_name="Название плейлиста")
    @is_admin()
    async def playlist_export(self, interaction: discord.Interaction, user_id: str, playlist_name: str):
        """Экспорт плейлиста"""
        try:
            user_id_int = int(user_id)
            playlist = self.load_playlist(user_id_int, playlist_name)
            
            if not playlist:
                await interaction.response.send_message(f"❌ Плейлист `{playlist_name}` не найден у пользователя {user_id}!")
                return
            
            # Создаем текстовый файл с плейлистом
            export_content = f"Плейлист: {playlist_name}\nПользователь: {user_id}\nТреков: {len(playlist)}\n\n"
            
            for i, song in enumerate(playlist, 1):
                export_content += f"{i}. {song.get('title', 'Неизвестно')}\n"
                export_content += f"   URL: {song.get('url', 'Нет ссылки')}\n"
                export_content += f"   Добавлено: {song.get('added_at', 'Неизвестно')}\n\n"
            
            # Сохраняем во временный файл
            export_filename = f"playlist_export_{user_id}_{playlist_name}.txt"
            export_path = os.path.join(PLAYLISTS_DIR, export_filename)
            
            with open(export_path, 'w', encoding='utf-8') as f:
                f.write(export_content)
            
            # Отправляем файл
            file = discord.File(export_path, filename=export_filename)
            await interaction.response.send_message(
                f"✅ Плейлист `{playlist_name}` пользователя {user_id} экспортирован!",
                file=file
            )
            
            # Удаляем временный файл
            os.remove(export_path)
            
        except ValueError:
            await interaction.response.send_message("❌ Неверный ID пользователя!")
        except Exception as e:
            await interaction.response.send_message(f"❌ Ошибка экспорта: {str(e)}")

async def setup(bot):
    await bot.add_cog(Playlist(bot))