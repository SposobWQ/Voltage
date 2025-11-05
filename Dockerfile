FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем куки файл если он существует
COPY youtube_cookies.json ./

COPY . .

RUN mkdir -p data/playlists

# СОЗДАЕМ ДИРЕКТОРИИ ДЛЯ ДАННЫХ (БЕЗ VOLUME)
RUN mkdir -p /app/data/playlists && \
    mkdir -p /tmp/music_bot/playlists && \
    chmod -R 755 /app/data /tmp/music_bot

ENV PYTHONUNBUFFERED=1
ENV PYTHONHTTPSVERIFY=0

CMD ["python", "main.py"]