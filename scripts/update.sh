#!/bin/bash
set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🔄 Starting application update..."

# Проверка Git
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git is not installed!${NC}"
    exit 1
fi

# Создание автоматического бэкапа перед обновлением
echo "💾 Creating backup before update..."
./scripts/backup.sh

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Backup failed! Aborting update.${NC}"
    exit 1
fi

# Сохранение изменений (если есть)
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}⚠️  You have uncommitted changes. Stashing them...${NC}"
    git stash
fi

# Получение обновлений
echo "📥 Pulling latest changes..."
git pull origin main

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Git pull failed!${NC}"
    exit 1
fi

# Пересборка контейнеров
echo "🔨 Rebuilding containers..."
docker-compose build --no-cache

# Остановка сервисов
echo "🛑 Stopping services..."
docker-compose down

# Запуск обновленных сервисов
echo "🚀 Starting updated services..."
docker-compose up -d

# Ожидание запуска базы данных
echo "⏳ Waiting for database..."
sleep 10

# Применение миграций
echo "📊 Applying database migrations..."
docker-compose exec -T backend python manage.py migrate --noinput

# Сбор статических файлов
echo "📦 Collecting static files..."
docker-compose exec -T backend python manage.py collectstatic --noinput --clear

# Проверка статуса
echo "✅ Checking services status..."
docker-compose ps

echo ""
echo -e "${GREEN}✅ Update completed successfully!${NC}"
echo ""
echo "Services are running:"
docker-compose ps

