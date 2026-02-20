"""Async SQLAlchemy engine & session factory for PostgreSQL."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession as SQLModelAsyncSession

from app.core.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=settings.app_debug,
    future=True,
)


async def get_session() -> AsyncGenerator[SQLModelAsyncSession, None]:
    """FastAPI dependency that yields an async DB session."""
    async with SQLModelAsyncSession(engine) as session:
        yield session


async def init_db() -> None:
    """Create pgvector extension and all tables (dev convenience)."""
    async with engine.begin() as conn:
        await conn.execute(
            # pgvector extension — safe to call repeatedly
            __import__("sqlalchemy").text("CREATE EXTENSION IF NOT EXISTS vector")
        )
        await conn.run_sync(SQLModel.metadata.create_all)
