#!/bin/sh
set -e

cd /app

if [ -n "$DATABASE_URL" ]; then
  case "$DATABASE_URL" in
    postgres://*)
      export DATABASE_URL="postgresql+asyncpg://${DATABASE_URL#postgres://}"
      ;;
    postgresql://*)
      export DATABASE_URL="postgresql+asyncpg://${DATABASE_URL#postgresql://}"
      ;;
  esac
fi

alembic upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
