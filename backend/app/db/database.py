"""
backend/app/db/database.py

Database connection setup using SQLAlchemy async engine.

We use an async engine because FastAPI is async — mixing sync
database calls into an async app causes performance problems.

Usage:
    async with get_session() as session:
        session.add(some_object)
        await session.commit()
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,       # set to True to log all SQL — useful for debugging
    pool_size=5,
    max_overflow=10,
)

SessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,  # keep objects accessible after commit
    class_=AsyncSession,
)


# ---------------------------------------------------------------------------
# Base class for all ORM models
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Session dependency — used in FastAPI routes
# ---------------------------------------------------------------------------

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


# ---------------------------------------------------------------------------
# Create all tables
# ---------------------------------------------------------------------------

async def create_tables() -> None:
    """Create all tables defined in ORM models. Called on app startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)