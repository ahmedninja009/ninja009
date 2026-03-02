# Dockerfile جاهز للبوت
FROM python:3.13-slim

# تحديث الحزم وتنصيب ffmpeg وcurl
RUN apt-get update && apt-get install -y ffmpeg curl && apt-get clean

# تعيين مجلد العمل
WORKDIR /app

# نسخ كل ملفات المشروع
COPY . /app

# تثبيت المكتبات المطلوبة
RUN pip install --no-cache-dir -r requirements.txt

# استخدام متغير البيئة للتوكن (لتجنب وضعه في الكود)
ENV TOKEN=""

# تشغيل البوت
CMD ["python", "main.py"]
