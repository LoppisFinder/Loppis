from contextlib import asynccontextmanager

import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import admin, crawl, loppis, meta, session
from app.services.crawl_scheduler import start_crawl_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler_task = start_crawl_scheduler()
    yield
    if scheduler_task:
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="LoppisFinder API",
    description="Hitta loppis i hela Sverige — anonymt och GDPR-vänligt",
    version="0.1.0",
    lifespan=lifespan,
)

cors_origins = settings.cors_origin_list
# Browsers reject Access-Control-Allow-Origin: * with credentials
allow_credentials = not (len(cors_origins) == 1 and cors_origins[0] == "*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(loppis.router)
app.include_router(session.router)
app.include_router(meta.router)
app.include_router(admin.router)
app.include_router(crawl.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "loppisfinder-api"}
