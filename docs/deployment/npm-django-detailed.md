# 🚀 Подробная настройка Nginx Proxy Manager для Django

## 📋 Содержание

1. [Предварительная проверка](#предварительная-проверка)
2. [Запуск NPM](#запуск-npm)
3. [Первая настройка веб-интерфейса](#первая-настройка-веб-интерфейса)
4. [Создание Proxy Host для Django](#создание-proxy-host-для-django)
5. [Настройка SSL сертификата](#настройка-ssl-сертификата)
6. [Проверка работы](#проверка-работы)
7. [Решение проблем](#решение-проблем)

---

## 🔍 Предварительная проверка

### Шаг 1.1: Проверка запущенного Django контейнера

```bash
# Проверить, что Django контейнер запущен
docker ps | grep backend

# Должен быть виден контейнер с именем iiko_backend
# Пример вывода:
# CONTAINER ID   IMAGE              STATUS         PORTS                    NAMES
# abc123def456   iiko_backend       Up 2 hours     0.0.0.0:8000->8000/tcp  iiko_backend
```

**Если контейнер не запущен:**
```bash
# Запустить Django
docker compose up -d backend

# Подождать 10-15 секунд и проверить снова
docker ps | grep backend
```

### Шаг 1.2: Проверка сети Docker

```bash
# Проверить существование сети
docker network ls | grep iiko_network

# Должен быть виден:
# abc123def456   iiko_network   bridge    local
```

**Если сети нет:**
```bash
# Создать сеть
docker network create iiko_network

# Или запустить основной docker-compose (сеть создастся автоматически)
docker compose up -d
```

### Шаг 1.3: Проверка доступности Django внутри сети

```bash
# Проверить, что Django доступен по имени контейнера
docker run --rm --network iiko_network curlimages/curl:latest curl -I http://iiko_backend:8000

# Должен вернуть HTTP 200 или 301/302 (редирект)
# Если ошибка - проверьте имя контейнера:
docker ps --format "table {{.Names}}\t{{.Status}}"
```

**Важно:** Запомните точное имя контейнера Django (обычно `iiko_backend`)

---

## 🚀 Запуск NPM

### Шаг 2.1: Проверка файла конфигурации

```bash
# Убедитесь, что файл существует
ls -la docker-compose.npm.yml

# Просмотрите содержимое (проверьте порты)
cat docker-compose.npm.yml | grep -A 5 "ports:"
```

**Для Synology порты должны быть:**
```yaml
ports:
  - '8080:80'    # HTTP
  - '8443:443'   # HTTPS
  - '81:81'      # Admin
```

### Шаг 2.2: Запуск NPM

```bash
# Перейти в директорию проекта (если еще не там)
cd /path/to/iiko-system-ready

# Запустить NPM
docker compose -f docker-compose.npm.yml up -d

# Вывод должен быть примерно таким:
# [+] Running 3/3
#  ✔ Container npm_db      Started
#  ✔ Container npm         Started
```

### Шаг 2.3: Проверка запуска

```bash
# Проверить статус контейнеров
docker compose -f docker-compose.npm.yml ps

# Должно быть:
# NAME      IMAGE                        STATUS
# npm       jc21/nginx-proxy-manager     Up X seconds
# npm_db    jc21/mariadb-aria            Up X seconds

# Проверить логи (должны быть без ошибок)
docker compose -f docker-compose.npm.yml logs --tail=50 npm
```

**Если есть ошибки:**
```bash
# Посмотреть полные логи
docker logs npm

# Проверить, не заняты ли порты
netstat -tuln | grep -E ":(80|443|81|8080|8443)"
# или на Linux
ss -tuln | grep -E ":(80|443|81|8080|8443)"
```

### Шаг 2.4: Проверка доступности веб-интерфейса

```bash
# Проверить доступность порта 81
curl -I http://localhost:81

# Должен вернуть HTTP 200
# Или откройте в браузере:
# http://ваш-ip-адрес:81
```

---

## 🌐 Первая настройка веб-интерфейса

### Шаг 3.1: Открытие веб-интерфейса

1. **Откройте браузер**
2. **Введите адрес:**
   ```
   http://ваш-ip-адрес:81
   ```
   или
   ```
   http://localhost:81
   ```

3. **Должна открыться страница входа NPM**

### Шаг 3.2: Первый вход

**Учетные данные по умолчанию:**
```
Email: admin@example.com
Password: changeme
```

**Визуально это выглядит так:**
```
┌─────────────────────────────────┐
│  Nginx Proxy Manager           │
│                                 │
│  Email: [admin@example.com]    │
│  Password: [changeme       ]   │
│                                 │
│         [ Sign In ]             │
└─────────────────────────────────┘
```

### Шаг 3.3: Изменение пароля (ОБЯЗАТЕЛЬНО!)

После входа:

1. **Нажмите на аватар** в правом верхнем углу (круг с инициалами)
2. **Выберите "Account Settings"** или "Настройки аккаунта"
3. **Измените:**
   - Email (на свой реальный)
   - Password (на надежный пароль)
4. **Нажмите "Save"**

**Важно:** Запишите новый пароль в безопасном месте!

---

## 🔗 Создание Proxy Host для Django

### Шаг 4.1: Открытие раздела Proxy Hosts

1. В левом меню найдите **"Hosts"** → **"Proxy Hosts"**
2. Нажмите кнопку **"Add Proxy Host"** (синяя кнопка справа вверху)

### Шаг 4.2: Настройка вкладки "Details"

**Заполните поля следующим образом:**

```
┌─────────────────────────────────────────────────┐
│ Details Tab                                     │
├─────────────────────────────────────────────────┤
│                                                 │
│ Domain Names:                                   │
│ ┌───────────────────────────────────────────┐ │
│ │ iiko.chaika.team                          │ │
│ └───────────────────────────────────────────┘ │
│                                                 │
│ Scheme:                                         │
│ ○ http  ● https                                │
│                                                 │
│ Forward Hostname / IP:                          │
│ ┌───────────────────────────────────────────┐ │
│ │ iiko_backend                              │ │
│ └───────────────────────────────────────────┘ │
│                                                 │
│ Forward Port:                                   │
│ ┌───────────────────────────────────────────┐ │
│ │ 8000                                      │ │
│ └───────────────────────────────────────────┘ │
│                                                 │
│ ☑ Cache Assets                                 │
│ ☑ Block Common Exploits                        │
│ ☑ Websockets Support                           │
│                                                 │
└─────────────────────────────────────────────────┘
```

**Пояснения к полям:**

- **Domain Names:** Ваш домен (например, `iiko.chaika.team`)
  - ⚠️ **Важно:** Домен должен указывать на IP вашего сервера!
  - Проверить можно командой: `nslookup iiko.chaika.team`

- **Scheme:** Оставьте `http` (SSL настроим отдельно)

- **Forward Hostname / IP:** Имя контейнера Django
  - ⚠️ **Важно:** Это должно быть **точное имя контейнера**!
  - Проверить: `docker ps --format "{{.Names}}" | grep backend`

- **Forward Port:** Порт Django (обычно `8000`)
  - Проверить: `docker ps | grep backend` (смотрите колонку PORTS)

- **Чекбоксы:**
  - ✅ **Cache Assets** - кэширование статики
  - ✅ **Block Common Exploits** - защита от атак
  - ✅ **Websockets Support** - поддержка WebSockets (если используете)

### Шаг 4.3: Проверка перед сохранением

**Перед нажатием "Save" проверьте:**

```bash
# 1. Проверить имя контейнера Django
docker ps --format "{{.Names}}" | grep backend
# Должно вывести: iiko_backend

# 2. Проверить доступность Django из сети
docker run --rm --network iiko_network curlimages/curl:latest \
  curl -I http://iiko_backend:8000
# Должен вернуть HTTP 200 или 301/302

# 3. Проверить DNS запись домена
nslookup iiko.chaika.team
# Должен показать IP вашего сервера
```

**Если что-то не работает - НЕ СОХРАНЯЙТЕ!** Исправьте сначала.

### Шаг 4.4: Сохранение Proxy Host

1. Нажмите кнопку **"Save"** внизу формы
2. Должно появиться уведомление об успешном создании
3. В списке Proxy Hosts появится новая запись

**Пока НЕ настраивайте SSL!** Сначала проверим работу без SSL.

---

## 🔒 Настройка SSL сертификата

### Шаг 5.1: Открытие настроек SSL

1. Найдите созданный Proxy Host в списке
2. Нажмите на **иконку карандаша (Edit)** справа от записи
3. Перейдите на вкладку **"SSL"**

### Шаг 5.2: Настройка Let's Encrypt

**Заполните форму:**

```
┌─────────────────────────────────────────────────┐
│ SSL Tab                                         │
├─────────────────────────────────────────────────┤
│                                                 │
│ SSL Certificate:                               │
│ ┌───────────────────────────────────────────┐ │
│ │ Request a new SSL Certificate with Let's  │ │
│ │ Encrypt                                   │ │
│ └───────────────────────────────────────────┘ │
│                                                 │
│ Email Address for Let's Encrypt:               │
│ ┌───────────────────────────────────────────┐ │
│ │ your-email@example.com                   │ │
│ └───────────────────────────────────────────┘ │
│                                                 │
│ ☑ I Agree to the Let's Encrypt Terms of Service│
│                                                 │
│ ☑ Force SSL                                    │
│ ☑ HTTP/2 Support                               │
│ ☑ HSTS Enabled                                 │
│ ☑ HSTS Subdomains                              │
│                                                 │
└─────────────────────────────────────────────────┘
```

**Пояснения:**

- **Email Address:** Ваш реальный email (для уведомлений о сертификате)
- **I Agree:** Обязательно отметьте!
- **Force SSL:** Автоматически перенаправляет HTTP на HTTPS
- **HTTP/2 Support:** Улучшает производительность
- **HSTS Enabled:** Защита от атак downgrade
- **HSTS Subdomains:** Применяет HSTS ко всем поддоменам

### Шаг 5.3: Требования для Let's Encrypt

**Перед запросом сертификата убедитесь:**

1. ✅ Домен указывает на IP вашего сервера
   ```bash
   nslookup iiko.chaika.team
   ```

2. ✅ Порт 80 открыт (для проверки Let's Encrypt)
   ```bash
   # Проверить, что порт 80 слушается
   netstat -tuln | grep :80
   # или для Synology (порт 8080)
   netstat -tuln | grep :8080
   ```

3. ✅ Порт 443 открыт (для HTTPS)
   ```bash
   netstat -tuln | grep :443
   # или для Synology (порт 8443)
   netstat -tuln | grep :8443
   ```

4. ✅ Firewall разрешает доступ к портам 80 и 443

### Шаг 5.4: Запрос сертификата

1. Заполните все поля
2. Нажмите **"Save"**
3. **Подождите 1-2 минуты** - NPM запросит сертификат у Let's Encrypt

**Что происходит:**
- NPM отправляет запрос в Let's Encrypt
- Let's Encrypt проверяет, что домен указывает на ваш сервер
- Если все ОК - сертификат выдается автоматически

### Шаг 5.5: Проверка статуса сертификата

1. Перейдите в **"SSL Certificates"** в левом меню
2. Найдите ваш домен в списке
3. Статус должен быть **"Valid"** (зеленый)

**Если статус "Invalid" или "Pending":**
- Проверьте логи: `docker logs npm | grep -i ssl`
- Убедитесь, что домен правильно настроен
- Проверьте, что порты открыты

---

## ✅ Проверка работы

### Шаг 6.1: Проверка через командную строку

```bash
# Проверка HTTP (должен редиректить на HTTPS)
curl -I http://iiko.chaika.team

# Должен вернуть:
# HTTP/1.1 301 Moved Permanently
# Location: https://iiko.chaika.team/...

# Проверка HTTPS
curl -I https://iiko.chaika.team

# Должен вернуть:
# HTTP/1.1 200 OK
# или
# HTTP/1.1 301/302 (редирект на /admin или другую страницу)
```

### Шаг 6.2: Проверка в браузере

1. Откройте `https://iiko.chaika.team` в браузере
2. **Проверьте:**
   - ✅ Страница загружается
   - ✅ В адресной строке есть замочек (🔒)
   - ✅ Сертификат валиден (нажмите на замочек для проверки)
   - ✅ Нет ошибок в консоли браузера (F12 → Console)

### Шаг 6.3: Проверка статики

```bash
# Проверка статических файлов
curl -I https://iiko.chaika.team/static/admin/css/base.css

# Должен вернуть HTTP 200
```

### Шаг 6.4: Проверка админки Django

1. Откройте `https://iiko.chaika.team/admin`
2. Должна открыться страница входа Django
3. Войдите с учетными данными суперпользователя

---

## 🐛 Решение проблем

### Проблема 1: "502 Bad Gateway"

**Симптомы:**
- В браузере видна ошибка "502 Bad Gateway"
- NPM не может подключиться к Django

**Решение:**

```bash
# 1. Проверить, что Django контейнер запущен
docker ps | grep backend

# 2. Проверить логи Django
docker logs iiko_backend --tail=50

# 3. Проверить доступность Django из сети
docker run --rm --network iiko_network curlimages/curl:latest \
  curl -v http://iiko_backend:8000

# 4. Проверить имя контейнера в настройках NPM
# Должно быть точно: iiko_backend
docker ps --format "{{.Names}}" | grep backend
```

**Частые причины:**
- Неправильное имя контейнера в NPM
- Django контейнер не в сети `iiko_network`
- Django не запущен или упал

### Проблема 2: SSL сертификат не выдается

**Симптомы:**
- В NPM статус сертификата "Invalid" или "Pending"
- Ошибки в логах про Let's Encrypt

**Решение:**

```bash
# 1. Проверить логи NPM
docker logs npm | grep -i "letsencrypt\|ssl\|certificate" | tail -20

# 2. Проверить DNS
nslookup iiko.chaika.team
# Должен показать IP вашего сервера

# 3. Проверить доступность порта 80 извне
# С другого компьютера или через онлайн-сервис:
curl -I http://iiko.chaika.team

# 4. Проверить firewall
# Убедитесь, что порты 80 и 443 открыты
```

**Частые причины:**
- Домен не указывает на IP сервера
- Порт 80 закрыт в firewall
- Превышен лимит запросов Let's Encrypt (5 в неделю на домен)

### Проблема 3: Статика не загружается (404)

**Симптомы:**
- Страница загружается, но нет CSS/JS
- В консоли браузера ошибки 404 для статики
- `https://iiko.chaika.team/static/assets/css/bootstrap.min.css` возвращает 404

**Решение:**

> 📖 **Подробное руководство:** См. [fix-static-404.md](fix-static-404.md)

**Быстрое решение:**

1. **Выполнить collectstatic:**
   ```bash
   docker compose exec backend python manage.py collectstatic --noinput
   ```

2. **Проверить доступность:**
   ```bash
   curl -I http://localhost:8000/static/assets/css/bootstrap.min.css
   ```

3. **Настроить NPM (если нужно):**
   - Откройте Proxy Host в NPM
   - Вкладка "Advanced"
   - Добавьте кастомную конфигурацию (см. раздел "Дополнительная настройка" ниже)
   - Сохраните и перезапустите NPM

**Если проблема сохраняется:**
- Добавьте кастомную конфигурацию Nginx в Advanced вкладке (см. ниже)

### Проблема 4: "Connection refused" или таймауты

**Симптомы:**
- Долгая загрузка страниц
- Ошибки подключения

**Решение:**

```bash
# 1. Проверить сеть
docker network inspect iiko_network

# 2. Проверить, что оба контейнера в сети
docker network inspect iiko_network | grep -A 5 "Containers"

# 3. Проверить пинг между контейнерами
docker exec npm ping -c 3 iiko_backend
```

---

## 🔧 Дополнительная настройка (Advanced)

### Настройка кастомной конфигурации Nginx

Если нужно настроить статику или медиа файлы отдельно:

1. Откройте Proxy Host в NPM
2. Перейдите на вкладку **"Advanced"**
3. Вставьте в поле **"Custom Nginx Configuration"**:

```nginx
# Увеличение таймаутов для больших запросов
proxy_connect_timeout 300s;
proxy_send_timeout 300s;
proxy_read_timeout 300s;

# Увеличение размера загружаемых файлов
client_max_body_size 100M;

# Статические файлы
location /static/ {
    proxy_pass http://iiko_backend:8000/static/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    expires 30d;
    add_header Cache-Control "public, immutable";
    access_log off;
}

# Медиа файлы
location /media/ {
    proxy_pass http://iiko_backend:8000/media/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    expires 7d;
    add_header Cache-Control "public";
}

# Основное приложение
location / {
    proxy_pass http://iiko_backend:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Host $host;
    proxy_redirect off;
}
```

4. Нажмите **"Save"**

---

## 📊 Мониторинг и логи

### Просмотр логов NPM

```bash
# Все логи
docker logs npm

# Последние 100 строк
docker logs npm --tail=100

# Логи в реальном времени
docker logs -f npm

# Логи с фильтром
docker logs npm 2>&1 | grep -i error
```

### Просмотр логов Django

```bash
# Логи Django
docker logs iiko_backend --tail=100

# Логи в реальном времени
docker logs -f iiko_backend
```

### Мониторинг в веб-интерфейсе NPM

1. **Dashboard** - общая статистика запросов
2. **Access Logs** - логи доступа (если включены)
3. **Audit Log** - история изменений

---

## ✅ Финальная проверка

После настройки выполните все проверки:

```bash
# 1. Проверка контейнеров
docker ps | grep -E "npm|backend"
# Должны быть запущены оба

# 2. Проверка сети
docker network inspect iiko_network | grep -A 3 "Containers"
# Оба контейнера должны быть в сети

# 3. Проверка доступности
curl -I https://iiko.chaika.team
# Должен вернуть HTTP 200

# 4. Проверка SSL
echo | openssl s_client -connect iiko.chaika.team:443 2>/dev/null | \
  openssl x509 -noout -dates
# Должен показать даты сертификата
```

---

## 🎯 Итоговая структура

```
Интернет
   ↓
[Ваш домен: iiko.chaika.team]
   ↓
[Роутер/Firewall]
   ↓ (порты 80, 443)
[Synology NAS]
   ↓ (порты 8080, 8443)
[Nginx Proxy Manager (npm)]
   ↓ (внутри Docker сети iiko_network)
[Django Backend (iiko_backend:8000)]
   ↓
[PostgreSQL (внешний сервер)]
```

---

## 📞 Дополнительная помощь

Если проблема не решена:

1. Соберите информацию:
   ```bash
   # Логи NPM
   docker logs npm > npm_logs.txt
   
   # Логи Django
   docker logs iiko_backend > django_logs.txt
   
   # Конфигурация сети
   docker network inspect iiko_network > network_info.txt
   ```

2. Проверьте документацию:
   - [NPM Official Docs](https://nginxproxymanager.com/guide/)
   - [Docker Networking](https://docs.docker.com/network/)

---

**Готово!** 🎉 Теперь ваш Django доступен через NPM с SSL!

