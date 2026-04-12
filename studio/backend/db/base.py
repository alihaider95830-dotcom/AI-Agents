from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from backend.core.config import settings


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy models."""


engine: AsyncEngine = create_async_engine(
    settings.async_database_url,
    pool_pre_ping=True,
)
