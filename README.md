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
| http://localhost:8080/ready | `database: ok` (миграции при старте api) |
| http://localhost:8080/docs | Swagger |
| http://localhost:15672 | RabbitMQ (`dws` / `dws_secret`) |

Проверка таблиц:

```powershell
docker compose exec postgres psql -U dws -d dws -c "\dt"
```

Ожидание: `download_jobs`, `downloaded_files`, `digit_stats_cache`.

Остановка: `docker compose down`

### Миграции вручную

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
$env:DATABASE_URL="postgresql+psycopg://dws:dws_secret@localhost:5432/dws"
alembic upgrade head
```

## Этапы

- **Этап 0:** каркас, Docker Compose, health/ping, React-заглушка
- **Этап 1:** domain-модели, SQLAlchemy, Alembic, репозитории, FileStorage, `/ready` проверяет БД
- **Этап 2:** клиент внешнего API (`ExternalCatalogClient`), Retry-After / 429 / 403, chunking ≤3
- **Этап 3 (текущий):** Celery `run_download_job`, Redis progress/lock, ZIP → storage → DB → mark downloaded

### Проверка этапа 3 (без UI)

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest -q tests/test_download_job_use_cases.py tests/test_zip_extractor.py -v
```

HTTP-эндпоинт старта job появится на этапе 4; сейчас логика проверяется unit-тестами use case.
