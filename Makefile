.PHONY: help build up down restart logs shell migrate makemigrations createsuperuser backup restore test

help: ## Показать эту справку
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Собрать все контейнеры
	docker-compose build

up: ## Запустить все сервисы
	docker-compose up -d

down: ## Остановить все сервисы
	docker-compose down

restart: ## Перезапустить все сервисы
	docker-compose restart

logs: ## Показать логи всех сервисов
	docker-compose logs -f

logs-backend: ## Показать логи backend
	docker-compose logs -f backend

logs-bot: ## Показать логи бота
	docker-compose logs -f bot

shell: ## Открыть bash в backend контейнере
	docker-compose exec backend bash

shell-db: ## Открыть psql в базе данных
	docker-compose exec postgres psql -U iiko_user -d iiko_db

migrate: ## Применить миграции
	docker-compose exec backend python manage.py migrate

makemigrations: ## Создать новые миграции
	docker-compose exec backend python manage.py makemigrations

createsuperuser: ## Создать суперпользователя
	docker-compose exec backend python manage.py createsuperuser

collectstatic: ## Собрать статические файлы
	docker-compose exec backend python manage.py collectstatic --noinput

backup: ## Создать резервную копию базы данных
	./scripts/backup.sh

restore: ## Восстановить базу данных из бэкапа
	@echo "Usage: make restore FILE=backups/postgres/backup_YYYYMMDD_HHMMSS.sql.gz"
	./scripts/restore.sh $(FILE)

test: ## Запустить тесты
	docker-compose exec backend python manage.py test

deploy: ## Развернуть приложение
	./scripts/deploy.sh

update: ## Обновить приложение
	./scripts/update.sh

ps: ## Показать статус контейнеров
	docker-compose ps

clean: ## Очистить все контейнеры и volumes
	docker-compose down -v
	docker system prune -f

dev: ## Запустить в режиме разработки
	docker-compose up

prod: ## Запустить в продакшн режиме
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

prod-down: ## Остановить продакшн
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml down

