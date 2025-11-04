FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    ca-certificates \
    opus-tools \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# СОЗДАЕМ ДИРЕКТОРИИ ДЛЯ ДАННЫХ
RUN mkdir -p /app/data/playlists && \
    mkdir -p /tmp/music_bot/playlists && \
    chmod -R 755 /app/data /tmp/music_bot

ENV PYTHONUNBUFFERED=1
ENV PYTHONHTTPSVERIFY=0
ENV FFMPEG_BINARY=ffmpeg

# Сообщаем Railway о томе для данных
VOLUME ["/app/data"]

CMD ["python", "main.py"]