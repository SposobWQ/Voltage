import discord
import yt_dlp
import asyncio
from config import YDL_OPTIONS, FFMPEG_OPTIONS

ytdl = yt_dlp.YoutubeDL(YDL_OPTIONS)

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
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        
        if 'entries' in data:
            data = data['entries'][0]
        
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **FFMPEG_OPTIONS), data=data)

    @classmethod
    async def search_songs(cls, query, limit=10):
        """Поиск песен"""
        loop = asyncio.get_event_loop()
        search_query = f"ytsearch{limit}:{query}"
        
        def extract():
            return ytdl.extract_info(search_query, download=False)
        
        data = await loop.run_in_executor(None, extract)
        return data.get('entries', []) if 'entries' in data else []

    @classmethod
    async def get_playlist_info(cls, url):
        """Получение информации о плейлисте"""
        loop = asyncio.get_event_loop()
        
        def extract():
            return ytdl.extract_info(url, download=False, process=False)
        
        return await loop.run_in_executor(None, extract)