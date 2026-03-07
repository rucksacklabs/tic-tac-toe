"""
Purpose: Database engine setup, session management, and base class.
Architecture: Persistence Layer (Infrastructure).
Notes: Supports asynchronous SQLAlchemy. Includes init_db for development/testing.
"""

from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.environment import Environment

DATABASE_URL = Environment.DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


# init_db() is intentionally kept for test isolation (in-memory SQLite via create_all).
# Production schema changes must go through Alembic migrations (make migrate).
async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
