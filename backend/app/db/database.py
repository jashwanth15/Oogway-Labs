import os
import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from backend.app.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

# Resolve database URL for async engine
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif db_url.startswith("postgresql://") and not db_url.startswith("postgresql+asyncpg://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# Ensure SQLite directory exists if using SQLite
if "sqlite" in db_url:
    os.makedirs("data", exist_ok=True)

try:
    engine = create_async_engine(
        db_url,
        echo=False,
        future=True,
        pool_pre_ping=True
    )
except Exception as e:
    logger.warning(f"Failed to create primary engine with {db_url}: {e}. Falling back to SQLite.")
    os.makedirs("data", exist_ok=True)
    fallback_url = "sqlite+aiosqlite:///./data/lenny_assistant.db"
    engine = create_async_engine(fallback_url, echo=False, future=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def init_db():
    """Initializes database tables."""
    global engine, AsyncSessionLocal
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info(f"Database initialized successfully with URL: {engine.url.render_as_string(hide_password=True)}")
    except Exception as e:
        logger.error(f"Error initializing primary database ({e}). Switching to local SQLite fallback.")
        os.makedirs("data", exist_ok=True)
        fallback_url = "sqlite+aiosqlite:///./data/lenny_assistant.db"
        engine = create_async_engine(fallback_url, echo=False, future=True)
        AsyncSessionLocal = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Local SQLite fallback initialized successfully.")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for obtaining async DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
