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
    async def from_url(cls, url, *, loop=None, stream=False, quality='medium'):
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
            error_msg = str(e)
            print(f"❌ Ошибка загрузки {url}: {error_msg}")
            
            # Если возрастное ограничение, пробуем альтернативный метод
            if any(x in error_msg.lower() for x in ['sign in to confirm your age', 'inappropriate', 'age restriction', 'confirm your age']):
                print("🔄 Пробуем обход возрастного ограничения через fallback...")
                return await cls.from_url_fallback(url, quality)
            else:
                raise Exception(f"Не удалось загрузить аудио: {error_msg}")

    @classmethod
    async def from_url_fallback(cls, url, quality='medium'):
        """Альтернативный метод для обхода возрастных ограничений"""
        fallback_options = {
            'format': 'bestaudio/best',
            'nocheckcertificate': True,
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 30,
            'age_limit': 100,
            'ignoreerrors': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'ios', 'web'],
                    'player_skip': ['configs', 'webpage', 'js'],
                }
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Mobile Safari/537.36',
            }
        }
        
        # Добавляем cookies если есть
        try:
            import os
            if os.path.exists('youtube_cookies.json'):
                fallback_options['cookiefile'] = 'youtube_cookies.json'
                print("🔑 Используем cookies в fallback методе")
        except:
            pass
        
        try:
            fallback_ytdl = yt_dlp.YoutubeDL(fallback_options)
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: fallback_ytdl.extract_info(url, download=False))
            
            if 'entries' in data:
                data = data['entries'][0]
            
            filename = data['url']
            ffmpeg_options = QUALITY_PRESETS.get(quality, FFMPEG_OPTIONS)
            
            audio_source = discord.FFmpegPCMAudio(
                filename,
                **ffmpeg_options,
                stderr=subprocess.PIPE
            )
            
            print("✅ Возрастное ограничение обойдено через fallback!")
            return cls(audio_source, data=data)
            
        except Exception as e:
            # Последняя попытка с минимальными настройками
            try:
                print("🔄 Последняя попытка с минимальными настройками...")
                minimal_options = {
                    'format': 'bestaudio/best',
                    'nocheckcertificate': True,
                    'quiet': True,
                    'no_warnings': True,
                }
                minimal_ytdl = yt_dlp.YoutubeDL(minimal_options)
                data = await loop.run_in_executor(None, lambda: minimal_ytdl.extract_info(url, download=False))
                
                if 'entries' in data:
                    data = data['entries'][0]
                
                filename = data['url']
                audio_source = discord.FFmpegPCMAudio(filename, **ffmpeg_options)
                
                print("✅ Успех через минимальные настройки!")
                return cls(audio_source, data=data)
                
            except Exception as final_error:
                raise Exception(f"Не удалось загрузить аудио после всех попыток: {str(final_error)}")

    @classmethod
    async def search_songs(cls, query, limit=10):
        """Поиск песен с обработкой возрастных ограничений"""
        loop = asyncio.get_event_loop()
        search_query = f"ytsearch{limit}:{query}"
        
        def extract():
            try:
                return ytdl.extract_info(search_query, download=False)
            except Exception as e:
                error_msg = str(e)
                print(f"❌ Ошибка поиска '{query}': {error_msg}")
                
                # Если возрастное ограничение при поиске, возвращаем пустой результат
                if any(x in error_msg.lower() for x in ['sign in to confirm your age', 'inappropriate', 'age restriction']):
                    print(f"⚠️ Возрастное ограничение при поиске '{query}', пропускаем...")
                    return {'entries': []}
                else:
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
                error_msg = str(e)
                print(f"❌ Ошибка получения плейлиста {url}: {error_msg}")
                
                # Если возрастное ограничение, возвращаем None
                if any(x in error_msg.lower() for x in ['sign in to confirm your age', 'inappropriate', 'age restriction']):
                    print(f"⚠️ Возрастное ограничение в плейлисте {url}")
                    return None
                else:
                    return None
        
        return await loop.run_in_executor(None, extract)

# Инициализация yt-dlp
try:
    ytdl = yt_dlp.YoutubeDL(YDL_OPTIONS)
    print("✅ yt-dlp инициализирован с улучшенным обходом ограничений")
    
except Exception as e:
    print(f"❌ Ошибка инициализации yt-dlp: {e}")
    # Аварийная инициализация
    minimal_options = {
        'format': 'bestaudio/best',
        'nocheckcertificate': True,
        'quiet': True,
        'no_warnings': True,
        'age_limit': 100,
        'ignoreerrors': True,
    }
    ytdl = yt_dlp.YoutubeDL(minimal_options)
    print("⚠️ yt-dlp инициализирован в аварийном режиме")