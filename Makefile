.PHONY: build up down test migrate shell logs lint format frontend-install frontend-add-component frontend-shell django-shell django-logs django-makemigrations django-createsuperuser logs-all restart-service django-exec dev rebuild

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

test:
	docker-compose run --rm web python manage.py test

migrate:
	docker-compose run --rm web python manage.py migrate

shell:
	docker-compose run --rm web python manage.py shell

logs:
	docker-compose logs -f

lint:
	docker-compose run --rm web flake8 .
	docker-compose run --rm web black . --check
	docker-compose run --rm web isort . --check-only

format:
	docker-compose run --rm web black .
	docker-compose run --rm web isort .

frontend-install:
	docker-compose run --rm frontend npm install

frontend-add-component:
	docker-compose run --rm frontend npx shadcn-ui add $(component)

frontend-shell:
	docker-compose run --rm frontend sh

# Nuevos comandos para Django
django-shell:
	docker-compose exec web bash

django-logs:
	docker-compose logs -f web

django-makemigrations:
	docker-compose run --rm web python manage.py makemigrations

django-createsuperuser:
	docker-compose run --rm web python manage.py createsuperuser

# Comando para ver los logs de todos los servicios
logs-all:
	docker-compose logs -f

# Comando para reiniciar un servicio específico
restart-service:
	docker-compose restart $(service)

# Comando para ejecutar un comando arbitrario en el contenedor de Django
django-exec:
	docker-compose exec web $(cmd)

# Comando para desarrollo con hot-reload
dev:
	docker-compose up

# Comando para reconstruir y reiniciar servicios
rebuild:
	docker-compose down
	docker-compose build
	docker-compose up -d