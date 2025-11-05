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

    # ... остальные методы остаются такими же как в предыдущей версии ...
    # [остальной код playlist.py остается без изменений]

async def setup(bot):
    await bot.add_cog(Playlist(bot))