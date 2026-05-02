#!/bin/bash
# Скрипт для получения SSL сертификатов Let's Encrypt для iiko.chaika.team

set -e

DOMAIN="iiko.chaika.team"
EMAIL="admin@chaika.team"  # Измените на свой email
SSL_DIR="./docker/nginx/ssl/${DOMAIN}"
CERTBOT_DIR="./docker/certbot"

echo "🔐 Настройка SSL сертификатов для ${DOMAIN}"
echo "================================================"

# Создаем необходимые директории
mkdir -p "${SSL_DIR}"
mkdir -p "${CERTBOT_DIR}/www"
mkdir -p "${CERTBOT_DIR}/conf"

# Проверяем, установлен ли certbot
if ! command -v certbot &> /dev/null; then
    echo "⚠️  Certbot не установлен. Устанавливаем..."
    
    if command -v apt-get &> /dev/null; then
        # Debian/Ubuntu
        sudo apt-get update
        sudo apt-get install -y certbot
    elif command -v yum &> /dev/null; then
        # CentOS/RHEL
        sudo yum install -y certbot
    else
        echo "❌ Не удалось определить пакетный менеджер"
        echo "Установите certbot вручную: https://certbot.eff.org/"
        exit 1
    fi
fi

# Проверяем, что домен указывает на этот сервер
echo ""
echo "📡 Проверяем DNS для ${DOMAIN}..."
SERVER_IP=$(curl -s ifconfig.me)
DOMAIN_IP=$(dig +short ${DOMAIN} | tail -n1)

if [ "$SERVER_IP" != "$DOMAIN_IP" ]; then
    echo "⚠️  ВНИМАНИЕ: DNS домена ${DOMAIN} (${DOMAIN_IP}) не совпадает с IP сервера (${SERVER_IP})"
    echo "Перед получением сертификата убедитесь, что:"
    echo "  1. A-запись для ${DOMAIN} указывает на ${SERVER_IP}"
    echo "  2. DNS изменения уже вступили в силу (может занять до 24 часов)"
    echo ""
    read -p "Продолжить получение сертификата? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Отменено"
        exit 1
    fi
fi

# Временно останавливаем nginx чтобы certbot мог использовать порт 80
echo ""
echo "🛑 Останавливаем Nginx..."
docker-compose stop nginx

# Получаем сертификат
echo ""
echo "📜 Получаем SSL сертификат от Let's Encrypt..."
sudo certbot certonly \
    --standalone \
    --non-interactive \
    --agree-tos \
    --email "${EMAIL}" \
    --domains "${DOMAIN}" \
    --cert-name "${DOMAIN}"

# Копируем сертификаты в директорию проекта
echo ""
echo "📋 Копируем сертификаты..."
sudo cp "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" "${SSL_DIR}/"
sudo cp "/etc/letsencrypt/live/${DOMAIN}/privkey.pem" "${SSL_DIR}/"
sudo cp "/etc/letsencrypt/live/${DOMAIN}/chain.pem" "${SSL_DIR}/" || true

# Устанавливаем правильные права доступа
sudo chown -R $(whoami):$(whoami) "${SSL_DIR}"
chmod 644 "${SSL_DIR}/fullchain.pem"
chmod 644 "${SSL_DIR}/chain.pem" 2>/dev/null || true
chmod 600 "${SSL_DIR}/privkey.pem"

# Запускаем nginx обратно
echo ""
echo "✅ Запускаем Nginx с SSL..."
docker-compose up -d nginx

# Настраиваем автоматическое обновление сертификатов
echo ""
echo "🔄 Настраиваем автоматическое обновление сертификатов..."

CRON_JOB="0 3 * * * certbot renew --quiet --post-hook 'cd $(pwd) && ./scripts/reload-nginx.sh'"
(crontab -l 2>/dev/null | grep -v "certbot renew"; echo "$CRON_JOB") | crontab -

echo ""
echo "✅ SSL сертификат успешно установлен!"
echo ""
echo "Информация о сертификате:"
echo "  Домен: ${DOMAIN}"
echo "  Путь к сертификатам: ${SSL_DIR}"
echo "  Email: ${EMAIL}"
echo ""
echo "Сертификат будет автоматически обновляться каждый день в 3:00"
echo ""
echo "🌐 Проверьте сайт: https://${DOMAIN}"
echo ""

