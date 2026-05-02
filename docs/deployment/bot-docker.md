# Запуск Telegram бота в отдельном Docker контейнере

## Обзор

Telegram бот может быть запущен как отдельный Docker контейнер, независимо от остальных сервисов системы.

## Структура файлов

- `docker-compose.bot.yml` - отдельный compose файл для бота
- `bot/Dockerfile` - Dockerfile для сборки образа бота
- `bot/requirements.txt` - Python зависимости бота

## Предварительные требования

1. **Сеть Docker**: Сеть `iiko_network` должна быть создана
   ```bash
   docker network create iiko_network
   ```
   Или запустите основной `docker-compose.yml` хотя бы один раз, чтобы создать сеть.

2. **Переменные окружения**: Убедитесь, что в `.env` файле установлены:
   ```env
   BOT_TOKEN=your-telegram-bot-token
   APP_HOST=http://iiko_backend:8000  # или внешний URL
   PUBLIC_URL=https://iiko.chaika.team
   DB_HOST=your-postgres-server.com
   DB_NAME=iiko_db
   DB_USERNAME=iiko_user
   DB_PASSWORD=your-password
   DB_PORT=5432
   ```

## Запуск бота отдельно

### Вариант 1: Использование отдельного compose файла (рекомендуется)

```bash
# Собрать образ бота
docker compose -f docker-compose.bot.yml build

# Запустить бота
docker compose -f docker-compose.bot.yml up -d

# Просмотр логов
docker compose -f docker-compose.bot.yml logs -f bot

# Остановить бота
docker compose -f docker-compose.bot.yml down
```

### Вариант 2: Запуск через основной docker-compose.yml

В основном `docker-compose.yml` бот помечен профилем `full`, поэтому:

```bash
# Запустить все сервисы включая бота
docker compose --profile full up -d

# Запустить только бота (если другие сервисы уже запущены)
docker compose up -d bot
```

## Пересборка образа

После изменения кода или зависимостей:

```bash
# Пересобрать образ без кэша
docker compose -f docker-compose.bot.yml build --no-cache

# Перезапустить бота
docker compose -f docker-compose.bot.yml up -d --force-recreate bot
```

## Проверка работы

1. **Проверка логов:**
   ```bash
   docker compose -f docker-compose.bot.yml logs -f bot
   ```

2. **Проверка статуса:**
   ```bash
   docker compose -f docker-compose.bot.yml ps
   ```

3. **Проверка в Telegram:**
   - Найдите вашего бота в Telegram
   - Отправьте команду `/start`
   - Должен прийти ответ с уникальным кодом

## Настройка для разработки

Для разработки можно смонтировать код бота:

1. Откройте `docker-compose.bot.yml`
2. Раскомментируйте строку:
   ```yaml
   volumes:
     - ./bot:/app
   ```
3. Перезапустите контейнер:
   ```bash
   docker compose -f docker-compose.bot.yml up -d --force-recreate bot
   ```

## Подключение к существующему backend

Если backend запущен в другом контейнере или на другом сервере:

1. Убедитесь, что оба контейнера в одной сети `iiko_network`
2. Установите `APP_HOST` в `.env`:
   ```env
   # Если backend в том же docker-compose
   APP_HOST=http://iiko_backend:8000
   
   # Если backend на другом сервере
   APP_HOST=http://your-backend-server.com:8000
   ```

## Устранение неполадок

### Бот не запускается

1. Проверьте логи:
   ```bash
   docker compose -f docker-compose.bot.yml logs bot
   ```

2. Проверьте переменные окружения:
   ```bash
   docker compose -f docker-compose.bot.yml config
   ```

3. Убедитесь, что `BOT_TOKEN` установлен:
   ```bash
   echo $BOT_TOKEN
   ```

### Ошибка подключения к backend

1. Проверьте, что backend доступен:
   ```bash
   docker compose ps backend
   ```

2. Проверьте сеть:
   ```bash
   docker network inspect iiko_network
   ```

3. Проверьте `APP_HOST` в переменных окружения

### Ошибка `AttributeError: module 'marshmallow' has no attribute '__version_info__'`

Убедитесь, что в `bot/requirements.txt` установлены правильные версии:
```
marshmallow==3.21.0
environs==11.0.0
```

Затем пересоберите образ:
```bash
docker compose -f docker-compose.bot.yml build --no-cache bot
```

## Мониторинг

Бот имеет healthcheck, который проверяет работоспособность каждые 30 секунд.

Проверить статус:
```bash
docker inspect iiko_bot | grep -A 10 Health
```

