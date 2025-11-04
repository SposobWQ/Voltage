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
        self.create_backup()

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
            
            # Проверяем свободное место (только на Linux)
            if hasattr(os, 'statvfs'):
                stat = os.statvfs(PLAYLISTS_DIR)
                free_gb = (stat.f_bavail * stat.f_frsize) / (1024 ** 3)
                storage_info['free_space'] = f"{free_gb:.1f} GB"
                
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
            for filename in os.listdir(PLAYLISTS_DIR):
                if filename.endswith('.json') and not filename.startswith('backup'):
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
                
                print(f"✅ Создана резервная копия {len(all_playlists)} плейлистов: {backup_file}")
                
                # Удаляем старые бэкапы (оставляем последние 3)
                backups = sorted([f for f in os.listdir(self.backup_dir) if f.startswith('playlists_backup_')])
                if len(backups) > 3:
                    for old_backup in backups[:-3]:
                        try:
                            os.remove(os.path.join(self.backup_dir, old_backup))
                            print(f"🗑️ Удален старый бэкап: {old_backup}")
                        except Exception as e:
                            print(f"❌ Ошибка удаления бэкапа {old_backup}: {e}")
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

    # ОБЩИЕ КОМАНДЫ (остаются без изменений)
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

    # ... остальные команды без изменений ...

    # НОВЫЕ КОМАНДЫ ДЛЯ МОНИТОРИНГА ХРАНИЛИЩА
    @app_commands.command(name="storage_info", description="Информация о хранилище (только для админов)")
    @is_admin()
    async def storage_info(self, interaction: discord.Interaction):
        """Информация о системе хранения"""
        embed = discord.Embed(
            title="💾 Информация о хранилище",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Директория", value=self.storage_info['playlists_dir'], inline=False)
        embed.add_field(name="Railway", value="Да" if self.storage_info['is_railway'] else "Нет")
        embed.add_field(name="Доступно для записи", value="✅ Да" if self.storage_info['writable'] else "❌ Нет")
        embed.add_field(name="Свободное место", value=self.storage_info['free_space'])
        
        # Информация о плейлистах
        playlists_info = self.get_all_playlists_info()
        total_playlists = sum(len(user_playlists) for user_playlists in playlists_info.values())
        total_users = len(playlists_info)
        
        embed.add_field(name="Всего пользователей", value=total_users)
        embed.add_field(name="Всего плейлистов", value=total_playlists)
        
        # Информация о бэкапах
        backups = sorted([f for f in os.listdir(self.backup_dir) if f.startswith('playlists_backup_')])
        embed.add_field(name="Резервных копий", value=len(backups))
        
        if backups:
            latest_backup = backups[-1]
            embed.add_field(name="Последний бэкап", value=latest_backup, inline=False)
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Playlist(bot))