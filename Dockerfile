FROM python:3.10-slim

# Устанавливаем FFmpeg и зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Проверяем установку FFmpeg
RUN ffmpeg -version

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p data/playlists

ENV PYTHONUNBUFFERED=1
ENV PYTHONHTTPSVERIFY=0

CMD ["python", "main.py"]