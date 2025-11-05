import discord
import yt_dlp
import asyncio
import subprocess
import time
import random
from config import YDL_OPTIONS, FFMPEG_OPTIONS

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration')
        self.thumbnail = data.get('thumbnail')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        
        # Случайная задержка чтобы избежать блокировки
        await asyncio.sleep(random.uniform(0.5, 2.0))
        
        try:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
            
            if 'entries' in data:
                data = data['entries'][0]
            
            filename = data['url'] if stream else ytdl.prepare_filename(data)
            
            # Проверяем доступность FFmpeg
            try:
                subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            except:
                raise Exception("FFmpeg не доступен!")
            
            audio_source = discord.FFmpegPCMAudio(
                filename,
                **FFMPEG_OPTIONS,
                stderr=subprocess.PIPE
            )
            
            return cls(audio_source, data=data)
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Ошибка загрузки {url}: {error_msg}")
            
            # Если блокировка Cloudflare
            if '429' in error_msg or 'rate limit' in error_msg.lower() or 'cloudflare' in error_msg.lower():
                raise Exception("🚫 Слишком много запросов. Подожди 1-2 минуты.")
            
            # Если возрастное ограничение
            elif any(x in error_msg for x in ['age-restricted', 'Sign in to confirm', 'inappropriate']):
                if YDL_OPTIONS.get('cookiefile'):
                    raise Exception("❌ Возрастное ограничение. Куки не работают.")
                else:
                    raise Exception("❌ Возрастное ограничение. Используйте куки файл.")
            else:
                raise Exception(f"Не удалось загрузить аудио: {error_msg}")

    @classmethod
    async def search_songs(cls, query, limit=10):
        """Поиск песен"""
        loop = asyncio.get_event_loop()
        search_query = f"ytsearch{limit}:{query}"
        
        # Случайная задержка
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        def extract():
            try:
                return ytdl.extract_info(search_query, download=False)
            except Exception as e:
                error_msg = str(e)
                print(f"❌ Ошибка поиска '{query}': {error_msg}")
                
                # Если блокировка Cloudflare
                if '429' in error_msg or 'rate limit' in error_msg.lower():
                    print("🚫 Блокировка Cloudflare - ждем...")
                    return {'entries': []}
                
                # Если возрастное ограничение при поиске
                elif any(x in error_msg for x in ['age-restricted', 'Sign in to confirm', 'inappropriate']):
                    print(f"⚠️ Возрастное ограничение при поиске '{query}'")
                    return {'entries': []}
                else:
                    return {'entries': []}
        
        data = await loop.run_in_executor(None, extract)
        return data.get('entries', []) if 'entries' in data else []

# Инициализация yt-dlp с обработкой ошибок
try:
    ytdl = yt_dlp.YoutubeDL(YDL_OPTIONS)
    print("✅ yt-dlp инициализирован с защитой от блокировки")
except Exception as e:
    print(f"❌ Ошибка инициализации yt-dlp: {e}")
    # Резервная инициализация с минимальными настройками
    ytdl = yt_dlp.YoutubeDL({
        'format': 'bestaudio/best',
        'nocheckcertificate': True,
        'quiet': True,
        'sleep_interval': 2,
    })