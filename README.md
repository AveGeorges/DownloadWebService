# Download Web Service

Сервис скачивания каталога текстовых файлов через внешнее API и расчёта статистики по цифрам.

## Стек

- Python 3.12, FastAPI, SQLAlchemy, Celery
- PostgreSQL, Redis, RabbitMQ
- React + Vite
- Nginx, Docker Compose
- Ruff, Pytest

## Структура

```
backend/          # API + worker (clean architecture layers)
frontend/         # React UI (Nginx в образе)
docker-compose.yml
```

## Алгоритм проверки и запуска

### 1. Backend без Docker (обязательная проверка этапа 0)

```powershell
.\scripts\check-backend.ps1
```

Или вручную:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
ruff check src tests
ruff format --check src tests
pytest -q
```

Ожидание: `All checks passed!`, `3 passed`.

Локальный API (опционально):

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --app-dir src --port 8000
```

Проверка: откройте `http://localhost:8000/health` во внешнем браузере → `{"status":"ok",...}`.

### 2. Полный стек в Docker (если запущен Docker Desktop)

```powershell
# 1) Убедиться, что Docker Desktop Running
docker info

# 2) Env и подъём
Copy-Item .env.example .env
docker compose up --build -d

# 3) Статус
docker compose ps

# 4) Проверки (внешний браузер / curl)
curl http://localhost:8080/health
curl http://localhost:8080/ready
curl http://localhost:8080/api/v1/ping
```

| URL | Что должно быть |
|-----|-----------------|
| http://localhost:8080 | UI-заглушка, бренд + кнопка «Скачать данные» |
| http://localhost:8080/health | `status: ok` |
| http://localhost:8080/docs | Swagger FastAPI |
| http://localhost:15672 | RabbitMQ management (`dws` / `dws_secret`) |

Остановка:

```powershell
docker compose down
```

Логи при проблемах:

```powershell
docker compose logs api worker frontend --tail=100
```

