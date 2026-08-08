from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# ─── Engine ─────────────────────────────────────────────────────────────────
engine = create_async_engine(
    "sqlite+aiosqlite:///./rightsizing.db",
    echo=settings.debug,
    connect_args={"check_same_thread": False}
)

# ─── Session factory ────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# ─── Base model ─────────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ─── Dependency ─────────────────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
