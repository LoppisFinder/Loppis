# LoppisFinder

Find loppis (garage sales) across Sweden on a map. Web + Android apps backed by multi-source crawlers.

## Stack

- **Web**: Next.js 15 + Leaflet
- **Mobile**: Expo (React Native)
- **API**: Python FastAPI + PostgreSQL/PostGIS
- **Crawlers**: Scrapy + Playwright
- **Workers**: Celery + Redis

## Quick start

### Prerequisites

- Node.js 20+, pnpm 9+
- Python 3.12+
- Docker & Docker Compose

### 1. Start infrastructure

```bash
cd infra
docker compose up -d
```

### 2. Install dependencies

```bash
pnpm install
cd services/api && pip install -r requirements.txt
cd ../crawler && pip install -r requirements.txt
cd ../worker && pip install -r requirements.txt
```

### 3. Run migrations

```bash
cd services/api
alembic upgrade head
python -m app.seed
```

### 4. Start services

```bash
# API (terminal 1)
pnpm dev:api

# Web (terminal 2)
pnpm dev:web

# Mobile (terminal 3)
pnpm dev:mobile
```

- Web: http://localhost:3000
- API: http://localhost:8000/docs

## Privacy

LoppisFinder uses anonymous sessions only — no email, names, or OAuth. See [docs/privacy.md](docs/privacy.md).
