FROM python:3.10-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Создаем рабочую директорию
WORKDIR /app

# Копируем requirements и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY . .

# Создаем пустой файл cookies при запуске
CMD ["python", "-c", \"\"\"
import json
import os
if not os.path.exists('youtube_cookies.json'):
    with open('youtube_cookies.json', 'w') as f:
        json.dump([], f)
    print('Created empty youtube_cookies.json')
import main
\"\"\""]