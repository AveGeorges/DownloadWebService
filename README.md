# Download Web Service

Сервис скачивания каталога текстовых файлов через внешнее API и расчёта статистики по цифрам.

## Стек

- Python 3.12, FastAPI, SQLAlchemy, Celery
- PostgreSQL, Redis, RabbitMQ
- React + Vite
- Nginx, Docker Compose
- Ruff, Pytest, Alembic

## Структура

```
backend/          # API + worker (clean architecture layers)
frontend/         # React UI (Nginx в образе)
docker-compose.yml
```

## Алгоритм проверки и запуска

### 1. Backend без Docker

```powershell
.\scripts\check-backend.ps1
```

Ожидание: `All checks passed!`, все тесты зелёные.

### 2. Полный стек в Docker

```powershell
docker info
Copy-Item .env.example .env
docker compose up --build -d
docker compose ps

curl.exe http://localhost:8080/health
curl.exe http://localhost:8080/ready
```

| URL | Ожидание |
|-----|----------|
| http://localhost:8080 | UI-заглушка |
| http://localhost:8080/health | `status: ok` |
| http://localhost:8080/ready | `database: ok` |
| http://localhost:8080/docs | Swagger |
| http://localhost:15672 | RabbitMQ (`dws` / `dws_secret`) |

### API этапа 4

```powershell
# Старт скачивания (нужен валидный EXTERNAL_API_BASE_URL)
curl.exe -X POST http://localhost:8080/api/v1/download-jobs

# Статус job
curl.exe http://localhost:8080/api/v1/download-jobs/<job_id>

# Список файлов
curl.exe "http://localhost:8080/api/v1/files?limit=20&offset=0"

# Все id
curl.exe -X POST http://localhost:8080/api/v1/files/select-all-ids

# Расчёты
curl.exe -X POST http://localhost:8080/api/v1/calculations -H "Content-Type: application/json" -d "{\"file_ids\":[\"...\"]}"
```

Остановка: `docker compose down`

## Этапы

- **Этап 0:** каркас, Docker Compose, health/ping, React-заглушка
- **Этап 1:** domain-модели, SQLAlchemy, Alembic, репозитории, FileStorage
- **Этап 2:** клиент внешнего API, Retry-After / 429 / 403
- **Этап 3:** Celery download job, Redis progress/lock
- **Этап 4 (текущий):** FastAPI — download-jobs, files, calculations
