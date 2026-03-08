from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

def _build_engine():
    url = settings.DATABASE_URL
    # SQLite needs check_same_thread=False; PostgreSQL doesn't support it
    if url.startswith("sqlite"):
        return create_async_engine(url, echo=False, connect_args={"check_same_thread": False})
    # Convert postgres:// to postgresql+asyncpg:// if Railway provides the old format
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return create_async_engine(url, echo=False)

engine = _build_engine()

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
