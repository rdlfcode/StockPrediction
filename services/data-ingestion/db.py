from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from config import settings

# Create async database engines
main_db_engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=False,
    future=True,
)

timescale_db_engine = create_async_engine(
    settings.TIMESCALEDB_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=False,
    future=True,
)

# Session factories
MainAsyncSessionLocal = sessionmaker(
    main_db_engine, class_=AsyncSession, expire_on_commit=False
)

TimeScaleAsyncSessionLocal = sessionmaker(
    timescale_db_engine, class_=AsyncSession, expire_on_commit=False
)

# Base model
Base = declarative_base()

# Session dependency
async def get_db_session():
    """Get an async session for the main database."""
    async with MainAsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def get_timescale_db_session():
    """Get an async session for the TimescaleDB database."""
    async with TimeScaleAsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()