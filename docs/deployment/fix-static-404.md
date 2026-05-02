# 🔧 Исправление 404 для статических файлов

## Проблема

Статические файлы не загружаются:
```
Request URL: https://iiko.chaika.team/static/assets/css/bootstrap.min.css
Status Code: 404 Not Found
```

## 🔍 Быстрая диагностика

Выполните эти команды по порядку:

```bash
# 1. Проверить, собрана ли статика
docker compose exec backend ls -la /app/staticfiles/static/assets/css/ 2>/dev/null | head -5

# 2. Проверить доступность напрямую от Django
curl -I http://localhost:8000/static/assets/css/bootstrap.min.css

# 3. Проверить через NPM
curl -I https://iiko.chaika.team/static/assets/css/bootstrap.min.css
```

## ✅ Решение (пошагово)

### Шаг 1: Сбор статики

```bash
# Выполнить collectstatic
docker compose exec backend python manage.py collectstatic --noinput

# Проверить результат
docker compose exec backend find /app/staticfiles -name "bootstrap.min.css" | head -3
```

**Ожидаемый результат:**
```
/app/staticfiles/static/assets/css/bootstrap.min.css
```

### Шаг 2: Проверка доступности от Django

```bash
# Проверить напрямую от Django (без NPM)
curl -I http://localhost:8000/static/assets/css/bootstrap.min.css
```

**Если возвращает 404:**
- Django не отдает статику в production
- Нужно добавить WhiteNoise или настроить NPM

**Если возвращает 200:**
- Проблема в настройке NPM
- Переходите к Шагу 3

### Шаг 3: Настройка NPM для статики

1. **Откройте NPM веб-интерфейс:**
   ```
   http://ваш-ip:81
   ```

2. **Найдите Proxy Host** для `iiko.chaika.team`

3. **Нажмите на иконку карандаша (Edit)**

4. **Перейдите на вкладку "Advanced"**

5. **В поле "Custom Nginx Configuration" вставьте:**

```nginx
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
    
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
    
    client_max_body_size 100M;
}
```

6. **Нажмите "Save"**

7. **Перезапустите NPM:**
   ```bash
   docker compose -f docker-compose.npm.yml restart nginx-proxy-manager
   ```

### Шаг 4: Проверка

```bash
# Подождите 10 секунд и проверьте
curl -I https://iiko.chaika.team/static/assets/css/bootstrap.min.css
```

**Должен вернуть:**
```
HTTP/2 200
content-type: text/css
```

## 🐛 Если проблема сохраняется

### Вариант A: Django не отдает статику

Если Django возвращает 404 даже напрямую, нужно добавить WhiteNoise:

1. **Установить WhiteNoise:**
   ```bash
   docker compose exec backend pip install whitenoise
   ```

2. **Обновить settings.py:**
   ```python
   MIDDLEWARE = [
       'django.middleware.security.SecurityMiddleware',
       'whitenoise.middleware.WhiteNoiseMiddleware',  # Добавить после SecurityMiddleware
       # ... остальные middleware
   ]
   
   # Добавить в конец settings.py
   STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
   ```

3. **Перезапустить:**
   ```bash
   docker compose restart backend
   docker compose exec backend python manage.py collectstatic --noinput
   ```

### Вариант B: Проверка volumes

```bash
# Проверить, что volume смонтирован
docker compose exec backend mount | grep staticfiles

# Проверить содержимое
docker compose exec backend ls -la /app/staticfiles/
```

### Вариант C: Полная пересборка

```bash
# 1. Остановить
docker compose stop backend

# 2. Пересобрать
docker compose build backend

# 3. Запустить
docker compose up -d backend

# 4. Собрать статику
docker compose exec backend python manage.py collectstatic --noinput

# 5. Проверить
docker compose exec backend ls -la /app/staticfiles/static/assets/css/ | head -5
```

## 📊 Проверка настроек Django

```bash
docker compose exec backend python manage.py shell
```

В Python shell:
```python
from django.conf import settings
import os

print("STATIC_URL:", settings.STATIC_URL)
print("STATIC_ROOT:", settings.STATIC_ROOT)
print("STATICFILES_DIRS:", settings.STATICFILES_DIRS)

# Проверить, существует ли файл
static_file = os.path.join(settings.STATIC_ROOT, "static", "assets", "css", "bootstrap.min.css")
print("File exists:", os.path.exists(static_file))
print("File path:", static_file)

exit()
```

## ✅ Финальная проверка

После всех исправлений:

```bash
# 1. Проверить статику напрямую
curl -I http://localhost:8000/static/assets/css/bootstrap.min.css

# 2. Проверить через NPM
curl -I https://iiko.chaika.team/static/assets/css/bootstrap.min.css

# 3. Открыть в браузере
# https://iiko.chaika.team
# Откройте DevTools (F12) → Network → перезагрузите страницу
# Проверьте, что статика загружается (статус 200)
```

## 📝 Чек-лист

- [ ] `collectstatic` выполнен
- [ ] Файлы существуют в `/app/staticfiles/static/`
- [ ] Django отдает статику напрямую (проверено curl)
- [ ] NPM настроен с кастомной конфигурацией
- [ ] NPM перезапущен
- [ ] Статика доступна через HTTPS

---

**После выполнения этих шагов статика должна работать!** ✅

