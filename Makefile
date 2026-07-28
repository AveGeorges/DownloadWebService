.PHONY: help env up down logs lint test build migrate

help:
	@echo "make env     - copy .env.example to .env"
	@echo "make up      - build and start stack (scripts/up.ps1 on Windows)"
	@echo "make down    - stop stack"
	@echo "make logs    - follow logs"
	@echo "make migrate - alembic upgrade head (local backend venv)"
	@echo "make lint    - ruff"
	@echo "make test    - pytest"
	@echo "make build   - docker compose build"

env:
	@if not exist .env copy .env.example .env

up: env
	powershell -ExecutionPolicy Bypass -File .\scripts\up.ps1

down:
	powershell -ExecutionPolicy Bypass -File .\scripts\down.ps1

logs:
	docker compose logs -f

migrate:
	cd backend && python -m alembic upgrade head

build:
	docker compose build

lint:
	cd backend && python -m ruff check src tests && python -m ruff format --check src tests

test:
	cd backend && python -m pytest -q
