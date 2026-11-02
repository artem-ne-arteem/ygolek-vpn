from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.config import Config
from bot.db.models import Base

_engine = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


async def init_db(config: Config) -> None:
    global _engine, _sessionmaker
    _engine = create_async_engine(config.database_url)
    _sessionmaker = async_sessionmaker(_engine, expire_on_commit=False)

    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def get_session():
    if _sessionmaker is None:
        raise RuntimeError("init_db() must be called before get_session()")
    async with _sessionmaker() as session:
        yield session
