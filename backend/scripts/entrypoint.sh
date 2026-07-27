#!/bin/sh
set -eu

if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
  echo "Running Alembic migrations..."
  alembic upgrade head
fi

exec "$@"
