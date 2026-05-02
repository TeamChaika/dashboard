#!/bin/bash
set -e

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Директория для бэкапов
BACKUP_DIR="./backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.sql"

# Создание директории если не существует
mkdir -p $BACKUP_DIR

echo "💾 Starting database backup..."

# Создание бэкапа базы данных
docker-compose exec -T postgres pg_dump -U iiko_user iiko_db > $BACKUP_FILE

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Database backup created: $BACKUP_FILE${NC}"
    
    # Сжатие бэкапа
    gzip $BACKUP_FILE
    echo -e "${GREEN}✅ Backup compressed: $BACKUP_FILE.gz${NC}"
    
    # Размер файла
    SIZE=$(du -h "$BACKUP_FILE.gz" | cut -f1)
    echo -e "${GREEN}📦 Backup size: $SIZE${NC}"
    
    # Удаление старых бэкапов (старше 30 дней)
    echo "🧹 Cleaning old backups (older than 30 days)..."
    find $BACKUP_DIR -name "*.gz" -mtime +30 -delete
    
    # Список последних 5 бэкапов
    echo ""
    echo "📋 Last 5 backups:"
    ls -lht $BACKUP_DIR/*.gz | head -n 5
    
else
    echo -e "${RED}❌ Backup failed!${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Backup completed successfully!${NC}"

