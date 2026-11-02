from contextlib import asynccontextmanager

from sqlalchemy import inspect, text
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
        await conn.run_sync(_add_missing_columns)


# create_all() не трогает уже существующие таблицы, поэтому новые колонки
# добираем руками. Работает и на SQLite, и на Postgres.
_NEW_COLUMNS = {
    "subscriptions": {
        "reminder_3d_sent": "BOOLEAN NOT NULL DEFAULT false",
        "expired_notified": "BOOLEAN NOT NULL DEFAULT false",
    },
}


def _add_missing_columns(sync_conn) -> None:
    inspector = inspect(sync_conn)
    for table, columns in _NEW_COLUMNS.items():
        existing = {col["name"] for col in inspector.get_columns(table)}
        for name, ddl in columns.items():
            if name not in existing:
                sync_conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))


@asynccontextmanager
async def get_session():
    if _sessionmaker is None:
        raise RuntimeError("init_db() must be called before get_session()")
    async with _sessionmaker() as session:
        yield session
