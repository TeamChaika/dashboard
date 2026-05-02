#!/bin/bash
# Скрипт для исправления проблем со статикой

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo "🔧 Исправление проблем со статикой..."
echo "======================================"

# 1. Пересобрать статику
echo ""
echo "📦 Пересборка статики..."
docker-compose exec backend python manage.py collectstatic --noinput --clear

# 2. Проверить права доступа
echo ""
echo "🔐 Проверка прав доступа..."
docker-compose exec backend ls -la /app/staticfiles/ | head -20

# 3. Проверить volume
echo ""
echo "💾 Проверка volume..."
docker volume inspect iiko-system-ready_static_volume

# 4. Перезапустить nginx
echo ""
echo "🔄 Перезапуск Nginx..."
docker-compose restart nginx

# 5. Проверить доступность статики
echo ""
echo "✅ Тестирование статики..."
sleep 3

# Проверка через curl
if curl -s -o /dev/null -w "%{http_code}" http://localhost/static/logo.png | grep -q "200"; then
    echo "✅ Статика доступна локально"
else
    echo "❌ Статика недоступна локально"
fi

# Проверка HTTPS
if command -v openssl &> /dev/null; then
    if curl -s -o /dev/null -w "%{http_code}" https://localhost/static/logo.png 2>/dev/null | grep -q "200"; then
        echo "✅ Статика доступна по HTTPS"
    else
        echo "⚠️  Статика недоступна по HTTPS (возможно, нет сертификатов)"
    fi
fi

# 6. Показать логи nginx
echo ""
echo "📋 Последние логи Nginx:"
docker-compose logs nginx --tail 20

echo ""
echo "✅ Готово!"
echo ""
echo "Проверьте статику в браузере:"
echo "  - http://iiko.chaika.team/static/logo.png"
echo "  - https://iiko.chaika.team/static/logo.png"
echo ""
echo "Если проблема сохраняется:"
echo "  1. Проверьте логи: docker-compose logs nginx"
echo "  2. Проверьте файлы: docker-compose exec nginx ls -la /var/www/static/"
echo "  3. Очистите кэш браузера (Ctrl+Shift+R)"
echo ""

