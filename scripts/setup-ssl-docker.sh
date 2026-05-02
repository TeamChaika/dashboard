#!/bin/bash
# Альтернативный скрипт для получения SSL через Docker (без установки certbot на хост)

set -e

DOMAIN="iiko.chaika.team"
EMAIL="admin@chaika.team"  # Измените на свой email
SSL_DIR="./docker/nginx/ssl/${DOMAIN}"

echo "🔐 Настройка SSL сертификатов через Docker для ${DOMAIN}"
echo "============================================================"

# Создаем необходимые директории
mkdir -p "${SSL_DIR}"
mkdir -p "./docker/certbot/www"
mkdir -p "./docker/certbot/conf"

# Проверяем DNS
echo ""
echo "📡 Проверяем DNS для ${DOMAIN}..."
SERVER_IP=$(curl -s ifconfig.me || echo "unknown")
echo "IP сервера: ${SERVER_IP}"
echo "Убедитесь, что A-запись для ${DOMAIN} указывает на этот IP"
echo ""

# Создаем временную конфигурацию nginx для получения сертификата
cat > ./docker/nginx/conf.d/certbot-temp.conf << 'EOF'
server {
    listen 80;
    server_name iiko.chaika.team;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 200 "Server is ready for SSL setup\n";
        add_header Content-Type text/plain;
    }
}
EOF

echo "🔄 Запускаем Nginx для получения сертификата..."
docker-compose down
docker-compose up -d nginx

# Ждем пока nginx запустится
sleep 5

# Получаем сертификат через certbot в Docker
echo ""
echo "📜 Получаем SSL сертификат от Let's Encrypt..."
docker run --rm \
    --name certbot \
    -v "$(pwd)/docker/certbot/conf:/etc/letsencrypt" \
    -v "$(pwd)/docker/certbot/www:/var/www/certbot" \
    -v "$(pwd)/${SSL_DIR}:/output" \
    -p 80:80 \
    certbot/certbot certonly \
    --standalone \
    --non-interactive \
    --agree-tos \
    --email "${EMAIL}" \
    --domains "${DOMAIN}" \
    --cert-name "${DOMAIN}"

# Копируем сертификаты
echo ""
echo "📋 Копируем сертификаты..."
docker run --rm \
    -v "$(pwd)/docker/certbot/conf:/etc/letsencrypt" \
    -v "$(pwd)/${SSL_DIR}:/output" \
    alpine:latest sh -c "
        cp /etc/letsencrypt/live/${DOMAIN}/fullchain.pem /output/ && \
        cp /etc/letsencrypt/live/${DOMAIN}/privkey.pem /output/ && \
        cp /etc/letsencrypt/live/${DOMAIN}/chain.pem /output/ || true && \
        chmod 644 /output/fullchain.pem && \
        chmod 600 /output/privkey.pem
    "

# Удаляем временную конфигурацию
rm -f ./docker/nginx/conf.d/certbot-temp.conf

# Перезапускаем с SSL конфигурацией
echo ""
echo "✅ Перезапускаем сервисы с SSL..."
docker-compose down
docker-compose up -d

echo ""
echo "✅ SSL сертификат успешно установлен!"
echo ""
echo "Информация о сертификате:"
echo "  Домен: ${DOMAIN}"
echo "  Путь: ${SSL_DIR}"
echo "  Email: ${EMAIL}"
echo ""
echo "🌐 Проверьте сайт: https://${DOMAIN}"
echo ""
echo "⚠️  Для автоматического обновления добавьте в crontab:"
echo "0 3 * * * cd $(pwd) && docker-compose run --rm certbot renew && ./scripts/reload-nginx.sh"
echo ""

