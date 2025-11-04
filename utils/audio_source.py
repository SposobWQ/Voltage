import discord
import yt_dlp
import asyncio
from config import YDL_OPTIONS, FFMPEG_OPTIONS
import ssl

# Попытка обойти SSL проблемы
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

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
            raise Exception(f"Ошибка при загрузке аудио: {str(e)}")

    @classmethod
    async def search_songs(cls, query, limit=10):
        """Поиск песен с обработкой ошибок"""
        loop = asyncio.get_event_loop()
        search_query = f"ytsearch{limit}:{query}"
        
        def extract():
            try:
                return ytdl.extract_info(search_query, download=False)
            except Exception as e:
                print(f"Ошибка поиска: {e}")
                return {'entries': []}
        
        data = await loop.run_in_executor(None, extract)
        return data.get('entries', []) if 'entries' in data else []

    @classmethod
    async def get_playlist_info(cls, url):
        """Получение информации о плейлисте с обработкой ошибок"""
        loop = asyncio.get_event_loop()
        
        def extract():
            try:
                return ytdl.extract_info(url, download=False, process=False)
            except Exception as e:
                print(f"Ошибка получения плейлиста: {e}")
                return None
        
        return await loop.run_in_executor(None, extract)

# Инициализация yt-dlp с обработкой ошибок
try:
    ytdl = yt_dlp.YoutubeDL(YDL_OPTIONS)
except Exception as e:
    print(f"Ошибка инициализации yt-dlp: {e}")
    # Резервные настройки
    YDL_OPTIONS['nocheckcertificate'] = True
    YDL_OPTIONS['ssl_verify'] = False
    ytdl = yt_dlp.YoutubeDL(YDL_OPTIONS)