#!/bin/sh
set -e

cd /app

if [ -z "$DATABASE_URL" ]; then
  echo "ERROR: DATABASE_URL is not set. Add your Neon connection string in Render Environment."
  exit 1
fi

echo "Running database migrations..."
attempt=1
while [ "$attempt" -le 5 ]; do
  if alembic upgrade head; then
    break
  fi
  if [ "$attempt" -eq 5 ]; then
    echo "ERROR: Database migration failed after 5 attempts."
    echo "Check: PostGIS enabled in Neon (CREATE EXTENSION postgis;) and DATABASE_URL is correct."
    exit 1
  fi
  echo "Migration attempt $attempt failed, retrying in 10s (Neon may be waking up)..."
  sleep 10
  attempt=$((attempt + 1))
done

echo "Starting API on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
