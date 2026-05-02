FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    libpq-dev \
    gettext \
    && rm -rf /var/lib/apt/lists/*

# Установка рабочей директории
WORKDIR /app

# Копирование requirements (не используется, зависимости установлены напрямую)
# COPY ../requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    Django==5.0.1 \
    djangorestframework==3.14.0 \
    django-extensions==3.2.3 \
    django-cors-headers==4.3.1 \
    django-filter==23.5 \
    drf-yasg==1.21.7 \
    django-silk==5.0.4 \
    django-debug-toolbar==4.2.0 \
    whitenoise==6.6.0 \
    gunicorn==21.2.0 \
    psycopg2-binary==2.9.9 \
    redis==5.0.1 \
    celery==5.3.4 \
    marshmallow==3.21.0 \
    environs==11.0.0 \
    pymemcache==4.0.0 \
    pandas==2.1.4 \
    numpy==1.26.3 \
    requests==2.32.5 \
    dicttoxml==1.7.16 \
    xmltodict==0.13.0 \
    openpyxl==3.1.2 \
    XlsxWriter==3.1.9 \
    python-dotenv==1.0.0 \
    pyTelegramBotAPI==4.15.2

# Копирование проекта
COPY . .

# Создание директорий
RUN mkdir -p /app/staticfiles /app/media /app/logs

# Сбор статики
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=dashboard.settings

# Открытие порта
EXPOSE 8000

# Запуск приложения
CMD ["gunicorn", "dashboard.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--threads", "2", "--timeout", "120"]

