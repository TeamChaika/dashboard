# 🔧 Пошаговое исправление 404 для статики

## Проблема

```
curl -I http://localhost:8000/static/assets/css/bootstrap.min.css
HTTP/1.1 404 Not Found
```

Статика не собрана в `/app/staticfiles/`.

## ✅ Решение (пошагово)

### Шаг 1: Проверка исходных файлов

```bash
# Проверить, что исходные файлы есть
docker compose exec backend ls -la /app/static/assets/css/bootstrap.min.css
```

**Ожидаемый результат:**
```
-rw-r--r-- 1 root root 123456 ... /app/static/assets/css/bootstrap.min.css
```

### Шаг 2: Проверка настроек Django

```bash
docker compose exec backend python manage.py shell
```

В Python shell выполните:
```python
from django.conf import settings
import os

print("STATIC_URL:", settings.STATIC_URL)
print("STATIC_ROOT:", settings.STATIC_ROOT)
print("STATICFILES_DIRS:", settings.STATICFILES_DIRS)

# Проверить существование директорий
print("STATIC_ROOT exists:", os.path.exists(settings.STATIC_ROOT))
print("STATICFILES_DIRS[0] exists:", os.path.exists(settings.STATICFILES_DIRS[0]))

exit()
```

**Ожидаемый результат:**
```
STATIC_URL: /static/
STATIC_ROOT: /app/staticfiles
STATICFILES_DIRS: ['/app/static']
STATIC_ROOT exists: True
STATICFILES_DIRS[0] exists: True
```

### Шаг 3: Сбор статики

```bash
# Выполнить collectstatic
docker compose exec backend python manage.py collectstatic --noinput

# Проверить результат
docker compose exec backend ls -la /app/staticfiles/static/assets/css/bootstrap.min.css
```

**Ожидаемый результат:**
```
-rw-r--r-- 1 root root 123456 ... /app/staticfiles/static/assets/css/bootstrap.min.css
```

### Шаг 4: Проверка доступности от Django

```bash
# Проверить напрямую от Django
curl -I http://localhost:8000/static/assets/css/bootstrap.min.css
```

**Если все еще 404:**

Django в production не отдает статику автоматически. Нужно либо:
- Добавить WhiteNoise (рекомендуется)
- Или настроить NPM для проксирования статики

### Шаг 5A: Добавление WhiteNoise (рекомендуется)

```bash
# 1. Установить WhiteNoise
docker compose exec backend pip install whitenoise

# 2. Обновить settings.py
docker compose exec backend python -c "
import re
with open('/app/dashboard/settings.py', 'r') as f:
    content = f.read()

# Добавить whitenoise в MIDDLEWARE после SecurityMiddleware
if 'whitenoise.middleware.WhiteNoiseMiddleware' not in content:
    content = re.sub(
        r\"('django\.middleware\.security\.SecurityMiddleware',)\",
        r\"\1\n    'whitenoise.middleware.WhiteNoiseMiddleware',\",
        content
    )
    
    # Добавить в конец файла
    if 'STATICFILES_STORAGE' not in content:
        content += '\n\n# WhiteNoise для статики\nSTATICFILES_STORAGE = \"whitenoise.storage.CompressedManifestStaticFilesStorage\"\n'
    
    with open('/app/dashboard/settings.py', 'w') as f:
        f.write(content)
print('Settings updated')
"

# 3. Перезапустить backend
docker compose restart backend

# 4. Пересобрать статику
docker compose exec backend python manage.py collectstatic --noinput

# 5. Проверить
curl -I http://localhost:8000/static/assets/css/bootstrap.min.css
```

**Ожидаемый результат:**
```
HTTP/1.1 200 OK
Content-Type: text/css
```

### Шаг 5B: Настройка NPM (альтернатива)

Если не хотите использовать WhiteNoise, настройте NPM:

1. Откройте NPM: `http://ваш-ip:81`
2. Найдите Proxy Host для `iiko.chaika.team`
3. Edit → Advanced
4. Вставьте в "Custom Nginx Configuration":

```nginx
location /static/ {
    proxy_pass http://iiko_backend:8000/static/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    expires 30d;
    add_header Cache-Control "public, immutable";
}

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

5. Save
6. Перезапустить NPM:
   ```bash
   docker compose -f docker-compose.npm.yml restart nginx-proxy-manager
   ```

### Шаг 6: Финальная проверка

```bash
# 1. Проверить от Django
curl -I http://localhost:8000/static/assets/css/bootstrap.min.css

# 2. Проверить через NPM
curl -I https://iiko.chaika.team/static/assets/css/bootstrap.min.css

# 3. Открыть в браузере
# https://iiko.chaika.team
# F12 → Network → перезагрузить → проверить статус статики
```

## 🐛 Если проблема сохраняется

### Проверка логов

```bash
# Логи Django
docker compose logs backend | grep -i static | tail -20

# Логи NPM
docker logs npm | grep -i static | tail -20
```

### Полная пересборка

```bash
# 1. Остановить
docker compose stop backend

# 2. Удалить старую статику
docker compose exec backend rm -rf /app/staticfiles/*

# 3. Запустить
docker compose up -d backend

# 4. Собрать статику
docker compose exec backend python manage.py collectstatic --noinput

# 5. Проверить
docker compose exec backend ls -la /app/staticfiles/static/assets/css/ | head -5
```

---

**После выполнения этих шагов статика должна работать!** ✅

