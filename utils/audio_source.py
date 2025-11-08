import discord
import yt_dlp
import asyncio
import subprocess
import random
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

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        
        print(f"🔗 Загрузка: {url}")
        
        # Задержка для избежания блокировок
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        try:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
            
            if 'entries' in data:
                data = data['entries'][0]
            
            filename = data['url'] if stream else ytdl.prepare_filename(data)
            
            # Проверяем FFmpeg
            try:
                subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            except:
                raise Exception("FFmpeg не доступен!")
            
            audio_source = discord.FFmpegPCMAudio(
                filename,
                **FFMPEG_OPTIONS,
                stderr=subprocess.PIPE
            )
            
            print(f"✅ Загружено: {data.get('title', 'Unknown')}")
            return cls(audio_source, data=data)
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Ошибка: {error_msg}")
            
            if any(x in error_msg for x in ['age-restricted', 'Sign in to confirm']):
                if YDL_OPTIONS.get('cookiefile'):
                    raise Exception("❌ Возрастное ограничение. Куки не сработали.")
                else:
                    raise Exception("❌ Возрастное ограничение. Нужны куки.")
            else:
                raise Exception(f"Ошибка загрузки: {error_msg}")

    @classmethod
    async def search_songs(cls, query, limit=10):
        """Поиск песен"""
        print(f"🔍 Поиск: '{query}'")
        loop = asyncio.get_event_loop()
        search_query = f"ytsearch{limit}:{query}"
        
        await asyncio.sleep(random.uniform(0.5, 1.0))
        
        def extract():
            try:
                return ytdl.extract_info(search_query, download=False)
            except Exception as e:
                error_msg = str(e)
                print(f"❌ Ошибка поиска: {error_msg}")
                return {'entries': []}
        
        data = await loop.run_in_executor(None, extract)
        results = data.get('entries', []) if 'entries' in data else []
        print(f"✅ Найдено результатов: {len(results)}")
        return results

    @classmethod
    async def get_playlist_info(cls, url):
        """Получение информации о плейлисте"""
        loop = asyncio.get_event_loop()
        
        def extract():
            try:
                return ytdl.extract_info(url, download=False)
            except Exception as e:
                print(f"❌ Ошибка получения информации о плейлисте: {e}")
                return None
        
        return await loop.run_in_executor(None, extract)

# Инициализация yt-dlp
try:
    ytdl = yt_dlp.YoutubeDL(YDL_OPTIONS)
    print("✅ yt-dlp инициализирован")
except Exception as e:
    print(f"❌ Ошибка yt-dlp: {e}")
    ytdl = yt_dlp.YoutubeDL({
        'format': 'bestaudio/best',
        'nocheckcertificate': True,
        'quiet': True,
    })

print("🎵 Audio_source готов!")