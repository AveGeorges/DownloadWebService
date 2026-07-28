FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/src

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system app \
    && useradd --system --gid app --create-home app

COPY pyproject.toml README.md ./
COPY src ./src
COPY alembic.ini ./
COPY alembic ./alembic
COPY scripts/entrypoint.sh /entrypoint.sh

RUN pip install --upgrade pip \
    && pip install . \
    && mkdir -p /data/files \
    && chmod +x /entrypoint.sh \
    && chown -R app:app /app /data /entrypoint.sh

USER app

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD [
    "uvicorn",
    "app.main:app",
    "--host",
    "0.0.0.0",
    "--port",
    "8000",
    "--timeout-graceful-shutdown",
    "30",
]
