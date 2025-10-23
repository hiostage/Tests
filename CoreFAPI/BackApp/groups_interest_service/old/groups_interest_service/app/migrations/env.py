import os
import sys
from logging.config import fileConfig
from alembic import context

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.models import Base
from app.db.session import async_engine

config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata

def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations():
    async with async_engine.connect() as connection:
        await connection.run_sync(do_run_migrations)

def run_migrations_online():
    import asyncio
    asyncio.run(run_async_migrations())

run_migrations_online()