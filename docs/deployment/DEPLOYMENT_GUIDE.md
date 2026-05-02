# 🚀 Полное руководство по развертыванию на сервере

## 📋 Что нужно загрузить на сервер

### Обязательные файлы и директории

```
iiko-system-ready/
├── app/
│   └── src/
│       ├── dashboard/          # Django приложение
│       │   ├── dashboard/
│       │   ├── authentication/
│       │   ├── waybills/
│       │   ├── writeoffs/
│       │   ├── stores/
│       │   ├── departments/
│       │   ├── spending/
│       │   ├── stats/
│       │   ├── core/
│       │   ├── static/         # Исходные статические файлы
│       │   ├── templates/
│       │   ├── manage.py
│       │   ├── Dockerfile
│       │   └── env.py
│       └── requirements.txt     # Общие зависимости (если есть)
├── bot/                        # Telegram бот
│   ├── bot.py
│   ├── env.py
│   ├── services.py
│   ├── Dockerfile
│   └── requirements.txt
├── docker-compose.yml          # Основной compose файл
├── docker-compose.bot.yml      # Compose для бота
├── docker-compose.npm.yml      # Compose для Nginx Proxy Manager
├── env.example                 # Пример переменных окружения
└── .env                        # Ваши реальные переменные (создать на сервере)
```

### Файлы, которые НЕ нужно загружать

- `.git/` - Git репозиторий
- `*.log` - Логи
- `__pycache__/` - Кэш Python
- `.venv/` - Виртуальное окружение
- `node_modules/` - Если есть
- `*.zip` - Архивы
- `docs/` - Документация (опционально)
- `*.md` - Markdown файлы (опционально, кроме README.md)

## 📤 Шаг 1: Подготовка файлов

### Вариант A: Через Git (рекомендуется)

```bash
# На сервере
cd /path/to/deployment
git clone https://your-repo/iiko-system-ready.git
cd iiko-system-ready
```

### Вариант B: Через SCP/SFTP

```bash
# С локального компьютера
scp -r iiko-system-ready/ user@server:/path/to/deployment/

# Или используйте FileZilla, WinSCP и т.д.
```

### Вариант C: Через архив

```bash
# На локальном компьютере
tar -czf iiko-system-ready.tar.gz \
  --exclude='.git' \
  --exclude='*.log' \
  --exclude='__pycache__' \
  --exclude='.venv' \
  --exclude='node_modules' \
  iiko-system-ready/

# Загрузить на сервер
scp iiko-system-ready.tar.gz user@server:/path/to/deployment/

# На сервере распаковать
cd /path/to/deployment
tar -xzf iiko-system-ready.tar.gz
cd iiko-system-ready
```

## ⚙️ Шаг 2: Настройка переменных окружения

```bash
# На сервере, в директории проекта
cp env.example .env
nano .env  # или vi .env
```

### Обязательные переменные для заполнения:

```env
# Django
SECRET_KEY=your-very-long-random-secret-key-here
ALLOWED_HOSTS=iiko.chaika.team,your-server-ip

# Database (внешний PostgreSQL)
DB_NAME=iiko_db
DB_USERNAME=iiko_user
DB_PASSWORD=your-strong-password
DB_HOST=your-postgres-server.com
DB_PORT=5432

# iiko API
IIKO_API_SERVER=https://api.iiko.ru
IIKO_API_USERNAME=your-iiko-username
IIKO_API_PASSWORD=your-iiko-password

# Telegram Bot
BOT_TOKEN=your-telegram-bot-token
APP_HOST=http://iiko_backend:8000
PUBLIC_URL=https://iiko.chaika.team

# Ports
BACKEND_PORT=8000
```

## 🐳 Шаг 3: Запуск Docker контейнеров

### 3.1: Создание сети Docker

```bash
# Создать сеть (если еще не создана)
docker network create iiko_network
```

### 3.2: Запуск основного приложения (Backend + Redis)

```bash
# Перейти в директорию проекта
cd /path/to/iiko-system-ready

# Запустить backend и redis
docker compose up -d

# Проверить статус
docker compose ps

# Проверить логи
docker compose logs -f backend
```

### 3.3: Запуск Telegram бота (опционально)

```bash
# Запустить бота отдельно
docker compose -f docker-compose.bot.yml up -d

# Проверить логи
docker compose -f docker-compose.bot.yml logs -f bot
```

### 3.4: Запуск Nginx Proxy Manager (опционально)

```bash
# Запустить NPM
docker compose -f docker-compose.npm.yml up -d

# Проверить статус
docker compose -f docker-compose.npm.yml ps

# Веб-интерфейс будет доступен на порту 81
# http://your-server-ip:81
```

## 🔧 Шаг 4: Первоначальная настройка Django

### 4.1: Создание суперпользователя

```bash
# Создать администратора
docker compose exec backend python manage.py createsuperuser

# Введите:
# Username: admin
# Email: admin@example.com
# Password: (надежный пароль)
```

### 4.2: Проверка миграций

```bash
# Проверить, что миграции применены
docker compose exec backend python manage.py showmigrations

# Если нужно применить миграции вручную
docker compose exec backend python manage.py migrate
```

### 4.3: Проверка статики

```bash
# Проверить, что статика собрана
docker compose exec backend ls -la /app/staticfiles/static/assets/css/ | head -5

# Если статика не собрана
docker compose exec backend python manage.py collectstatic --noinput
```

## ✅ Шаг 5: Проверка работы

### 5.1: Проверка Backend

```bash
# Проверить доступность Django
curl -I http://localhost:8000

# Должен вернуть HTTP 200 или 301/302
```

### 5.2: Проверка статики

```bash
# Проверить статику
curl -I http://localhost:8000/static/assets/css/bootstrap.min.css

# Должен вернуть HTTP 200
```

### 5.3: Проверка в браузере

1. Откройте `http://your-server-ip:8000` или `https://iiko.chaika.team`
2. Должна открыться страница входа
3. Войдите с учетными данными суперпользователя

## 🔒 Шаг 6: Настройка Nginx Proxy Manager (если используете)

См. подробную инструкцию: [npm-django-detailed.md](npm-django-detailed.md)

Кратко:
1. Откройте `http://your-server-ip:81`
2. Войдите: `admin@example.com` / `changeme`
3. Создайте Proxy Host для `iiko.chaika.team`
4. Настройте SSL через Let's Encrypt

## 📝 Чек-лист развертывания

- [ ] Файлы загружены на сервер
- [ ] Создан `.env` файл с правильными переменными
- [ ] Создана сеть `iiko_network`
- [ ] Backend контейнер запущен
- [ ] Redis контейнер запущен
- [ ] Миграции применены
- [ ] Статика собрана
- [ ] Создан суперпользователь
- [ ] Backend доступен на порту 8000
- [ ] Статика загружается (проверено curl)
- [ ] Бот запущен (если нужен)
- [ ] NPM настроен (если используете)

## 🔄 Обновление приложения

После изменений в коде:

```bash
# 1. Остановить контейнеры
docker compose stop backend

# 2. Пересобрать образ
docker compose build backend

# 3. Запустить
docker compose up -d backend

# 4. Применить миграции (если есть новые)
docker compose exec backend python manage.py migrate

# 5. Собрать статику (если изменилась)
docker compose exec backend python manage.py collectstatic --noinput

# 6. Проверить логи
docker compose logs -f backend
```

## 🐛 Устранение неполадок

### Проблема: Контейнеры не запускаются

```bash
# Проверить логи
docker compose logs

# Проверить конфигурацию
docker compose config

# Пересобрать без кэша
docker compose build --no-cache
```

### Проблема: База данных недоступна

```bash
# Проверить переменные окружения
docker compose exec backend env | grep DB_

# Проверить подключение
docker compose exec backend python manage.py dbshell
```

### Проблема: Статика не загружается

```bash
# Собрать статику
docker compose exec backend python manage.py collectstatic --noinput

# Проверить директорию
docker compose exec backend ls -la /app/staticfiles/static/
```

---

**Готово! Приложение должно работать.** ✅

