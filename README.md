# Download Web Service

Сервис скачивания каталога текстовых файлов через внешнее API и расчёта статистики по цифрам.

## Стек

- Python 3.12, FastAPI, SQLAlchemy, Celery
- PostgreSQL, Redis, RabbitMQ
- React + Vite
- Nginx, Docker Compose
- Ruff, Pytest, Alembic

## Быстрый старт

```powershell
Copy-Item .env.example .env
# Укажите реальный EXTERNAL_API_BASE_URL и X_CANDIDATE_ID
docker compose up --build -d
```

UI: http://localhost:8080  
Swagger: http://localhost:8080/docs

## Проверки backend

```powershell
.\scripts\check-backend.ps1
```

## Проверка frontend

```powershell
cd frontend
npm install
npm run build
```

## UI (этап 5)

- Кнопка **«Скачать данные»** в шапке на любой странице
- Прогресс: старт по НСК, «получено N названий, скачиваю/скачано M из N»
- Список файлов: имя, время (НСК), пагинация
- Выбор: точечно / страница / все; **«Произвести расчёты»**
- Результаты: общая статистика 0–9 и таблица по файлам

## API

| Method | Path | Назначение |
|--------|------|------------|
| POST | `/api/v1/download-jobs` | Старт скачивания |
| GET | `/api/v1/download-jobs/{id}` | Статус/прогресс |
| GET | `/api/v1/files` | Список файлов |
| POST | `/api/v1/files/select-all-ids` | Все id |
| POST | `/api/v1/calculations` | Статистика цифр |

## Этапы

- **0:** каркас + Docker
- **1:** модели + Alembic
- **2:** внешний API-клиент
- **3:** Celery download job
- **4:** FastAPI endpoints
- **5 (текущий):** React UI
