import discord
import yt_dlp
import asyncio
import subprocess
import random
import time
from config import YDL_OPTIONS, FFMPEG_OPTIONS

print("🎵 Инициализация audio_source...")

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration')
        self.thumbnail = data.get('thumbnail')
        print(f"🎵 Создан аудио источник: {self.title}")

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        
        print(f"🔗 Загрузка аудио из: {url}")
        
        # Случайная задержка чтобы избежать блокировки
        delay = random.uniform(0.5, 2.0)
        print(f"⏳ Задержка {delay:.1f} сек...")
        await asyncio.sleep(delay)
        
        try:
            print("📥 Извлечение информации о видео...")
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
            
            if 'entries' in data:
                data = data['entries'][0]
                print("📋 Из плейлиста взят первый трек")
            
            filename = data['url'] if stream else ytdl.prepare_filename(data)
            print(f"💾 Файл: {filename}")
            
            # Проверяем доступность FFmpeg
            try:
                result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    print("✅ FFmpeg доступен для обработки")
                else:
                    raise Exception("FFmpeg вернул ошибку")
            except Exception as e:
                print(f"❌ Ошибка FFmpeg: {e}")
                raise Exception("FFmpeg не доступен!")
            
            print("🎧 Создание аудио источника...")
            audio_source = discord.FFmpegPCMAudio(
                filename,
                **FFMPEG_OPTIONS,
                stderr=subprocess.PIPE
            )
            
            print("✅ Аудио источник успешно создан")
            return cls(audio_source, data=data)
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Ошибка загрузки {url}: {error_msg}")
            
            # Если блокировка Cloudflare
            if '429' in error_msg or 'rate limit' in error_msg.lower() or 'cloudflare' in error_msg.lower():
                print("🚫 Обнаружена блокировка Cloudflare")
                raise Exception("🚫 Слишком много запросов. Подожди 1-2 минуты.")
            
            # Если возрастное ограничение
            elif any(x in error_msg for x in ['age-restricted', 'Sign in to confirm', 'inappropriate']):
                if YDL_OPTIONS.get('cookiefile'):
                    print("🔞 Возрастное ограничение - куки не сработали")
                    raise Exception("❌ Возрастное ограничение. Куки не работают.")
                else:
                    print("🔞 Возрастное ограничение - куки не настроены")
                    raise Exception("❌ Возрастное ограничение. Используйте куки файл.")
            else:
                print("💥 Неизвестная ошибка при загрузке")
                raise Exception(f"Не удалось загрузить аудио: {error_msg}")

    @classmethod
    async def search_songs(cls, query, limit=10):
        """Поиск песен"""
        print(f"🔍 Поиск: '{query}' (лимит: {limit})")
        loop = asyncio.get_event_loop()
        search_query = f"ytsearch{limit}:{query}"
        
        # Случайная задержка
        delay = random.uniform(0.5, 1.5)
        print(f"⏳ Задержка поиска {delay:.1f} сек...")
        await asyncio.sleep(delay)
        
        def extract():
            try:
                print("📡 Выполнение поискового запроса...")
                return ytdl.extract_info(search_query, download=False)
            except Exception as e:
                error_msg = str(e)
                print(f"❌ Ошибка поиска '{query}': {error_msg}")
                
                # Если блокировка Cloudflare
                if '429' in error_msg or 'rate limit' in error_msg.lower():
                    print("🚫 Блокировка Cloudflare при поиске")
                    return {'entries': []}
                
                # Если возрастное ограничение при поиске
                elif any(x in error_msg for x in ['age-restricted', 'Sign in to confirm', 'inappropriate']):
                    print(f"🔞 Возрастное ограничение при поиске '{query}'")
                    return {'entries': []}
                else:
                    print("💥 Другая ошибка при поиске")
                    return {'entries': []}
        
        data = await loop.run_in_executor(None, extract)
        results = data.get('entries', []) if 'entries' in data else []
        print(f"✅ Найдено {len(results)} результатов по запросу '{query}'")
        return results

# Инициализация yt-dlp с обработкой ошибок
print("🔄 Инициализация yt-dlp...")
try:
    ytdl = yt_dlp.YoutubeDL(YDL_OPTIONS)
    print("✅ yt-dlp инициализирован с защитой от блокировки")
except Exception as e:
    print(f"❌ Ошибка инициализации yt-dlp: {e}")
    print("🔄 Резервная инициализация yt-dlp...")
    # Резервная инициализация с минимальными настройками
    ytdl = yt_dlp.YoutubeDL({
        'format': 'bestaudio/best',
        'nocheckcertificate': True,
        'quiet': True,
        'sleep_interval': 2,
    })
    print("✅ yt-dlp инициализирован в резервном режиме")

print("🎵 Audio_source модуль готов!")