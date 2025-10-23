import os
import sys
from logging.config import fileConfig
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import AsyncConnection
import asyncio

# Добавляем корень проекта в PYTHONPATH
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

from alembic import context
from app.core.config import settings
from app.models.base import Base  # Импортируем Base из models/base.py

# Загружаем конфиг alembic.ini
config = context.config
fileConfig(config.config_file_name)

# Это нужно для автогенерации миграций
target_metadata = Base.metadata

# Создаём асинхронный движок
engine = create_async_engine(settings.DATABASE_URL, echo=True)


async def run_migrations_online():
    """Асинхронное выполнение миграций"""
    async with engine.begin() as connection:
        await connection.run_sync(do_run_migrations)


def do_run_migrations(connection: AsyncConnection):
    """Настройка контекста и запуск миграций"""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True
    )

    with context.begin_transaction():
        context.run_migrations()


# Запуск миграций в асинхронном контексте
asyncio.run(run_migrations_online())
