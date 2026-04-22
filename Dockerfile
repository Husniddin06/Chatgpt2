FROM python:3.11-slim

# ffmpeg ovozli xabarlarni qayta ishlash uchun kerak
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Avval requirements.txt ni nusxalash (Docker layer cache uchun)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Qolgan kodni nusxalash
COPY . .

# Muhim: PYTHONPATH /app bo'lishi kerak, shunda 'from bot.database import db' kabi importlar ishlaydi
ENV PYTHONPATH=/app

# Botni modul sifatida ishga tushirish (bot/main.py to'g'ridan-to'g'ri emas)
CMD ["python", "-m", "bot.main"]
