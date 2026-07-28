# Download Web Service

Сервис скачивания каталога текстовых файлов через внешнее API и расчёта статистики по цифрам.

## Стек

Python 3.12 · FastAPI · SQLAlchemy · Celery · PostgreSQL · Redis · RabbitMQ · React · Nginx · Docker

## One-command demo

```powershell
Copy-Item .env.example .env
# Отредактируйте EXTERNAL_API_BASE_URL и X_CANDIDATE_ID
.\scripts\up.ps1
```

| URL | Что |
|-----|-----|
| http://localhost:8080 | UI |
| http://localhost:8080/docs | Swagger |
| http://localhost:8080/ready | Postgres + Redis + RabbitMQ |
| http://localhost:15672 | RabbitMQ UI (`dws` / `dws_secret`) |

Остановка: `.\scripts\down.ps1`

## Проверки качества / CI

Локально:

```powershell
.\scripts\check-backend.ps1   # ruff + pytest + coverage (>=70%)

cd frontend
npm ci
npm run build
```

CI: `.github/workflows/ci.yml` — backend (ruff/pytest/coverage) и frontend (build) на push/PR.

## Архитектура (кратко)

```
Browser → Nginx (frontend) → FastAPI (api)
                              ↘ Celery worker ← RabbitMQ
                              ↘ PostgreSQL / Redis / files volume
```

## API

| Method | Path | Назначение |
|--------|------|------------|
| POST | `/api/v1/download-jobs` | Старт скачивания |
| GET | `/api/v1/download-jobs/{id}` | Статус/прогресс |
| GET | `/api/v1/files` | Список файлов |
| POST | `/api/v1/files/select-all-ids` | Все id |
| POST | `/api/v1/calculations` | Статистика цифр |

## Этапы

0 каркас → 1 модели → 2 API-клиент → 3 Celery job → 4 FastAPI → 5 React UI → 6 Docker/Nginx → **7 тесты + CI**
