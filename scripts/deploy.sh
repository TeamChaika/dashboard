#!/bin/bash
set -e

echo "🚀 Starting deployment..."

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Проверка наличия Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Проверка наличия Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Проверка наличия .env файла
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from example...${NC}"
    cp env.example .env
    echo -e "${YELLOW}⚠️  Please edit .env file with your configuration before continuing.${NC}"
    exit 1
fi

# Создание необходимых директорий
echo "📁 Creating directories..."
mkdir -p docker/nginx/ssl
mkdir -p backups/postgres
mkdir -p app/logs

# Остановка существующих контейнеров
echo "🛑 Stopping existing containers..."
docker-compose down

# Удаление старых образов
echo "🧹 Cleaning up old images..."
docker-compose rm -f

# Сборка новых образов
echo "🔨 Building new images..."
docker-compose build --no-cache

# Запуск контейнеров
echo "🚀 Starting containers..."
docker-compose up -d

# Ожидание запуска базы данных
echo "⏳ Waiting for database to be ready..."
sleep 10

# Применение миграций
echo "📊 Applying database migrations..."
docker-compose exec -T backend python manage.py migrate --noinput

# Сбор статических файлов
echo "📦 Collecting static files..."
docker-compose exec -T backend python manage.py collectstatic --noinput --clear

# Проверка статуса сервисов
echo "✅ Checking services status..."
docker-compose ps

# Вывод информации
echo ""
echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo ""
echo "📍 Services are available at:"
echo "   - Backend: http://localhost:8000"
echo "   - Admin Panel: http://localhost:8000/admin"
echo "   - Health Check: http://localhost/health/"
echo ""
echo "📝 View logs:"
echo "   docker-compose logs -f"
echo ""
echo "🛠️  Useful commands:"
echo "   docker-compose ps          - Check services status"
echo "   docker-compose logs -f     - View logs"
echo "   docker-compose restart     - Restart all services"
echo "   docker-compose down        - Stop all services"
echo ""

