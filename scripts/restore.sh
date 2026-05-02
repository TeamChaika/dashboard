#!/bin/bash
set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Проверка аргумента
if [ -z "$1" ]; then
    echo -e "${RED}❌ Usage: $0 <backup_file.sql.gz>${NC}"
    echo ""
    echo "Available backups:"
    ls -lht ./backups/postgres/*.gz 2>/dev/null | head -n 10
    exit 1
fi

BACKUP_FILE=$1

# Проверка существования файла
if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}❌ Backup file not found: $BACKUP_FILE${NC}"
    exit 1
fi

echo -e "${YELLOW}⚠️  WARNING: This will overwrite the current database!${NC}"
echo -e "${YELLOW}⚠️  Make sure you have a recent backup before proceeding.${NC}"
echo ""
read -p "Are you sure you want to restore from $BACKUP_FILE? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

echo "💾 Starting database restore..."

# Создание временного файла
TEMP_FILE="/tmp/restore_$(date +%s).sql"

# Распаковка бэкапа
echo "📦 Decompressing backup..."
gunzip -c $BACKUP_FILE > $TEMP_FILE

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to decompress backup!${NC}"
    exit 1
fi

# Остановка зависимых сервисов
echo "🛑 Stopping dependent services..."
docker-compose stop backend bot

# Восстановление базы данных
echo "📊 Restoring database..."
docker-compose exec -T postgres psql -U iiko_user -d iiko_db < $TEMP_FILE

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Database restored successfully!${NC}"
    
    # Удаление временного файла
    rm $TEMP_FILE
    
    # Запуск сервисов
    echo "🚀 Starting services..."
    docker-compose start backend bot
    
    # Применение миграций (на случай обновлений)
    echo "📊 Applying migrations..."
    docker-compose exec backend python manage.py migrate --noinput
    
    echo ""
    echo -e "${GREEN}✅ Restore completed successfully!${NC}"
    echo ""
    echo "Services status:"
    docker-compose ps
else
    echo -e "${RED}❌ Restore failed!${NC}"
    rm $TEMP_FILE
    
    # Попытка запустить сервисы в любом случае
    docker-compose start backend bot
    exit 1
fi

