# Настройка Nginx Proxy Manager на Synology

> ⚠️ **Важно:** Для подробной пошаговой инструкции по настройке NPM для Django см. [npm-django-detailed.md](npm-django-detailed.md)

## Проблема с портами

На Synology порты **80** и **443** заняты системным веб-сервером DSM. Поэтому Nginx Proxy Manager настроен на альтернативные порты.

## Используемые порты

- **8080** → HTTP (вместо 80)
- **8443** → HTTPS (вместо 443)
- **81** → Веб-интерфейс управления NPM

## Запуск

```bash
# Запустить Nginx Proxy Manager
docker compose -f docker-compose.npm.yml up -d

# Проверить статус
docker compose -f docker-compose.npm.yml ps

# Просмотр логов
docker compose -f docker-compose.npm.yml logs -f
```

## Доступ к интерфейсу

1. **Веб-интерфейс NPM:**
   ```
   http://your-synology-ip:81
   ```

2. **Первоначальные учетные данные:**
   - Email: `admin@example.com`
   - Password: `changeme`
   
   ⚠️ **Сразу после первого входа измените пароль!**

## Настройка прокси для Django

После входа в NPM создайте новый Proxy Host:

1. **Details:**
   - Domain Names: `iiko.chaika.team` (или ваш домен)
   - Scheme: `http`
   - Forward Hostname/IP: `iiko_backend` (имя контейнера Django)
   - Forward Port: `8000`
   - ✅ Block Common Exploits
   - ✅ Websockets Support

2. **SSL:**
   - Request a new SSL Certificate
   - ✅ Force SSL
   - ✅ HTTP/2 Support
   - ✅ HSTS Enabled

## Настройка Synology Reverse Proxy (альтернатива)

Если вы хотите использовать стандартные порты 80/443, можно настроить Reverse Proxy в DSM:

1. Откройте **Control Panel** → **Login Portal** → **Advanced** → **Reverse Proxy**
2. Создайте правило:
   - **Source:**
     - Protocol: `HTTPS`
     - Hostname: `iiko.chaika.team`
     - Port: `443`
   - **Destination:**
     - Protocol: `HTTPS`
     - Hostname: `localhost`
     - Port: `8443`

3. Аналогично для HTTP (80 → 8080)

## Проверка работы

```bash
# Проверить, что контейнеры запущены
docker ps | grep npm

# Проверить логи
docker logs npm
docker logs npm_db

# Проверить доступность
curl http://localhost:8080
curl -k https://localhost:8443
```

## Устранение неполадок

### Порт уже занят

Если порт 8080 или 8443 занят, измените их в `docker-compose.npm.yml`:

```yaml
ports:
  - '8081:80'    # Измените 8080 на другой порт
  - '8444:443'   # Измените 8443 на другой порт
```

### Не могу подключиться к интерфейсу

1. Проверьте, что контейнер запущен:
   ```bash
   docker ps | grep npm
   ```

2. Проверьте логи:
   ```bash
   docker logs npm
   ```

3. Проверьте, что порт 81 открыт в Synology Firewall

### SSL сертификаты не работают

1. Убедитесь, что домен указывает на IP вашего Synology
2. Проверьте, что порты 80 и 443 открыты в роутере (для Let's Encrypt)
3. В NPM используйте порты 8080/8443 для проверки, но настройте Reverse Proxy в DSM для внешнего доступа

## Дополнительные настройки

### Изменение портов через переменные окружения

Можно использовать переменные окружения в `.env`:

```env
NPM_HTTP_PORT=8080
NPM_HTTPS_PORT=8443
NPM_ADMIN_PORT=81
```

И обновить `docker-compose.npm.yml`:

```yaml
ports:
  - '${NPM_HTTP_PORT:-8080}:80'
  - '${NPM_HTTPS_PORT:-8443}:443'
  - '${NPM_ADMIN_PORT:-81}:81'
```

