import discord
import yt_dlp
import asyncio
import ssl
import subprocess
from config import YDL_OPTIONS, FFMPEG_OPTIONS, QUALITY_PRESETS

ssl._create_default_https_context = ssl._create_unverified_context

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration')
        self.thumbnail = data.get('thumbnail')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False, quality='high'):
        loop = loop or asyncio.get_event_loop()
        try:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
            
            if 'entries' in data:
                data = data['entries'][0]
            
            filename = data['url'] if stream else ytdl.prepare_filename(data)
            
            # Используем настройки качества
            ffmpeg_options = QUALITY_PRESETS.get(quality, FFMPEG_OPTIONS)
            
            audio_source = discord.FFmpegPCMAudio(
                filename,
                **ffmpeg_options,
                stderr=subprocess.PIPE
            )
            
            return cls(audio_source, data=data)
        except Exception as e:
            print(f"❌ Ошибка загрузки {url}: {e}")
            raise Exception(f"Не удалось загрузить аудио: {str(e)}")

    @classmethod
    async def search_songs(cls, query, limit=10):
        loop = asyncio.get_event_loop()
        search_query = f"ytsearch{limit}:{query}"
        
        def extract():
            try:
                return ytdl.extract_info(search_query, download=False)
            except Exception as e:
                print(f"❌ Ошибка поиска '{query}': {e}")
                return {'entries': []}
        
        data = await loop.run_in_executor(None, extract)
        return data.get('entries', []) if 'entries' in data else []

    @classmethod
    async def get_playlist_info(cls, url):
        loop = asyncio.get_event_loop()
        
        def extract():
            try:
                return yt_dlp.YoutubeDL(YDL_OPTIONS).extract_info(url, download=False, process=False)
            except Exception as e:
                print(f"❌ Ошибка получения плейлиста {url}: {e}")
                return None
        
        return await loop.run_in_executor(None, extract)

# Инициализация yt-dlp
try:
    ytdl = yt_dlp.YoutubeDL(YDL_OPTIONS)
    print("✅ yt-dlp инициализирован")
except Exception as e:
    print(f"❌ Ошибка инициализации yt-dlp: {e}")