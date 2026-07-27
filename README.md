# Download Web Service

Сервис скачивания каталога текстовых файлов через внешнее API и расчёта статистики по цифрам.

## Стек

Python 3.12 · FastAPI · SQLAlchemy · Celery · PostgreSQL · Redis · RabbitMQ · React · Nginx · Docker

## One-command demo

```powershell
# 1) Env
Copy-Item .env.example .env
# Отредактируйте EXTERNAL_API_BASE_URL и X_CANDIDATE_ID

# 2) Подъём всего стека
.\scripts\up.ps1
```

Или вручную: `docker compose up --build -d`

| URL | Что |
|-----|-----|
| http://localhost:8080 | UI |
| http://localhost:8080/docs | Swagger |
| http://localhost:8080/ready | Postgres + Redis + RabbitMQ |
| http://localhost:15672 | RabbitMQ UI (`dws` / `dws_secret`) |

Остановка: `.\scripts\down.ps1`

Postgres/Redis/AMQP **не проброшены** на хост (только внутренняя сеть Docker). Снаружи — UI `:8080` и RabbitMQ management `:15672`.

## Проверки качества

```powershell
.\scripts\check-backend.ps1

cd frontend
npm install
npm run build
```

## Архитектура (кратко)

```
Browser → Nginx (frontend) → FastAPI (api)
                              ↘ Celery worker ← RabbitMQ
                              ↘ PostgreSQL / Redis / files volume
```

Кнопка «Скачать данные» → `POST /api/v1/download-jobs` → Celery качает каталог пачками ≤3 с учётом 429/403 → файлы в volume + БД → UI показывает список и считает цифры.

## Переменные (.env)

| Переменная | Назначение |
|------------|------------|
| `EXTERNAL_API_BASE_URL` | Базовый URL внешнего API задания |
| `X_CANDIDATE_ID` | Идентификатор кандидата |
| `POSTGRES_*` / `DATABASE_URL` | БД |
| `REDIS_URL` | Прогресс job + result backend |
| `CELERY_BROKER_URL` | RabbitMQ |
| `FILES_STORAGE_PATH` | Путь к файлам в контейнере (`/data/files`) |

## API

| Method | Path | Назначение |
|--------|------|------------|
| POST | `/api/v1/download-jobs` | Старт скачивания |
| GET | `/api/v1/download-jobs/{id}` | Статус/прогресс |
| GET | `/api/v1/files` | Список файлов |
| POST | `/api/v1/files/select-all-ids` | Все id |
| POST | `/api/v1/calculations` | Статистика цифр |

## Этапы

0 каркас → 1 модели → 2 API-клиент → 3 Celery job → 4 FastAPI → 5 React UI → **6 Docker/Nginx demo**
