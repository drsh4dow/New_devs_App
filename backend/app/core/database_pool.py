from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from ..config import settings

# Connections are opened lazily and shared across revenue requests.
engine = create_async_engine(
    make_url(settings.database_url).set(drivername="postgresql+asyncpg"),
    pool_pre_ping=True,
)
session_factory = async_sessionmaker(engine, expire_on_commit=False)
