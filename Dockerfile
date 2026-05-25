# Використовуємо офіційний, полегшений образ Python 3.10
FROM python:3.10-slim

# Встановлюємо системні залежності, необхідні для компіляції mysqlclient
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Вказуємо робочу директорію всередині контейнера
WORKDIR /app

# Копіюємо файл залежностей та встановлюємо їх
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Копіюємо весь інший код нашого проєкту
COPY . .