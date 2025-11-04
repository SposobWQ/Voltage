import discord
import yt_dlp
import asyncio
import ssl
import urllib3
from config import YDL_OPTIONS, FFMPEG_OPTIONS

# ГЛОБАЛЬНЫЙ SSL ФИКС
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
        try:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
            
            if 'entries' in data:
                data = data['entries'][0]
            
            filename = data['url'] if stream else ytdl.prepare_filename(data)
            return cls(discord.FFmpegPCMAudio(filename, **FFMPEG_OPTIONS), data=data)
        except Exception as e:
            print(f"❌ Ошибка загрузки {url}: {e}")
            # Пробуем упрощенный метод как запасной вариант
            return await cls.simple_download(url)

    @classmethod
    async def simple_download(cls, url):
        """Упрощенный метод загрузки как запасной вариант"""
        simple_options = {
            'format': 'bestaudio/best',
            'nocheckcertificate': True,
            'quiet': True,
            'no_warnings': True,
        }
        try:
            simple_ytdl = yt_dlp.YoutubeDL(simple_options)
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: simple_ytdl.extract_info(url, download=False))
            
            if 'entries' in data:
                data = data['entries'][0]
            
            return cls(discord.FFmpegPCMAudio(data['url'], **FFMPEG_OPTIONS), data=data)
        except Exception as e:
            raise Exception(f"Не удалось загрузить аудио: {str(e)}")

    @classmethod
    async def search_songs(cls, query, limit=10):
        """Поиск песен с обработкой SSL ошибок"""
        loop = asyncio.get_event_loop()
        search_query = f"ytsearch{limit}:{query}"
        
        def extract():
            try:
                return ytdl.extract_info(search_query, download=False)
            except Exception as e:
                error_msg = str(e)
                if "SSL" in error_msg or "CERTIFICATE" in error_msg:
                    print(f"🔒 SSL ошибка проигнорирована, возвращаем пустой результат")
                    return {'entries': []}
                print(f"❌ Ошибка поиска: {e}")
                return {'entries': []}
        
        data = await loop.run_in_executor(None, extract)
        return data.get('entries', []) if 'entries' in data else []

# Инициализация yt-dlp
try:
    ytdl = yt_dlp.YoutubeDL(YDL_OPTIONS)
    print("✅ yt-dlp инициализирован")
except Exception as e:
    print(f"❌ Ошибка yt-dlp: {e}")