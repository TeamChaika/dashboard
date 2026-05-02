#!/bin/bash
# Скрипт для перезагрузки Nginx после обновления SSL сертификатов

set -e

DOMAIN="iiko.chaika.team"
SSL_DIR="./docker/nginx/ssl/${DOMAIN}"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$PROJECT_DIR"

echo "🔄 Обновляем SSL сертификаты в проекте..."

# Копируем обновленные сертификаты
sudo cp "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" "${SSL_DIR}/"
sudo cp "/etc/letsencrypt/live/${DOMAIN}/privkey.pem" "${SSL_DIR}/"
sudo cp "/etc/letsencrypt/live/${DOMAIN}/chain.pem" "${SSL_DIR}/" || true

# Устанавливаем правильные права
sudo chown -R $(whoami):$(whoami) "${SSL_DIR}"
chmod 644 "${SSL_DIR}/fullchain.pem"
chmod 644 "${SSL_DIR}/chain.pem" 2>/dev/null || true
chmod 600 "${SSL_DIR}/privkey.pem"

# Перезапускаем nginx
echo "🔄 Перезапускаем Nginx..."
docker-compose restart nginx

echo "✅ SSL сертификаты обновлены, Nginx перезапущен"

