import os
from urllib.parse import urlparse
from typing import AsyncGenerator
import logging
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Настройка логирования
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Конфигурация БД
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable must be set")

# Валидация URL
parsed = urlparse(SQLALCHEMY_DATABASE_URL)
if not parsed.scheme.startswith('postgresql'):
    raise ValueError("Invalid database URL scheme")

# Используем асинхронный драйвер asyncpg
if SQLALCHEMY_DATABASE_URL.startswith("postgresql://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Создание асинхронного движка
engine: AsyncEngine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_pre_ping=True
)

# Создание асинхронной сессии
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Асинхронный генератор сессий для Dependency Injection"""
    async with AsyncSessionLocal() as session:
        yield session