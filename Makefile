.PHONY: help env up down logs lint test api-shell build

help:
	@echo "make env       - copy .env.example to .env"
	@echo "make up        - build and start the full stack"
	@echo "make down      - stop and remove containers"
	@echo "make logs      - follow container logs"
	@echo "make lint      - run ruff check + format check"
	@echo "make test      - run backend pytest"
	@echo "make build     - build images only"
	@echo "make api-shell - shell into api container"

env:
	@if not exist .env copy .env.example .env

up: env
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f

build:
	docker compose build

lint:
	cd backend && python -m ruff check src tests && python -m ruff format --check src tests

test:
	cd backend && python -m pytest -q

api-shell:
	docker compose exec api sh
