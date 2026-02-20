"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.db.engine import init_db


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Run startup / shutdown hooks."""
    import logging
    logger = logging.getLogger("app.startup")

    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as exc:
        logger.warning("Could not connect to database on startup: %s", exc)
        logger.warning("The server will start, but DB-dependent endpoints will fail.")
    yield


app = FastAPI(
    title="Talk to Your Data",
    description="Voice-native Agentic RAG system",
    version="0.1.0",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────

app.include_router(v1_router)
