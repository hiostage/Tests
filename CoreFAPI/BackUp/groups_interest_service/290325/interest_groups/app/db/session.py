import os
from urllib.parse import urlparse
from typing import Generator
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

# Настройка логгирования
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

# Тестовая среда
if os.getenv("TESTING"):
    SQLALCHEMY_DATABASE_URL += "_test"

# Создание engine с настройками пула
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """Генератор сессий для Dependency Injection"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()