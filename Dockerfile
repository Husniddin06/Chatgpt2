FROM python:3.11-slim

# ffmpeg ovozli xabarlarni qayta ishlash uchun kerak
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Avval requirements.txt ni nusxalash
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Butun loyihani nusxalash
COPY . .

# PYTHONPATH ni /app qilib belgilash va bot papkasini ham qo'shish
ENV PYTHONPATH=/app:/app/bot

# Botni ishga tushirish (modul sifatida va to'g'ridan-to'g'ri fayl sifatida sinab ko'rish)
# Railway uchun eng ishonchli usul:
CMD ["python", "bot/main.py"]
