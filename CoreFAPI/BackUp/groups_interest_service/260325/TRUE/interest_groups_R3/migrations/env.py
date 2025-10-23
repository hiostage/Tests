import os
import sys
from logging.config import fileConfig
from sqlalchemy import create_engine

# Добавляем корень проекта в PYTHONPATH
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

from alembic import context
from app.db.session import SQLALCHEMY_DATABASE_URL
from app.models.base import Base  # Импортируем Base из models/base.py

# Это нужно для автогенерации миграций
target_metadata = Base.metadata

def run_migrations_online():
    connectable = create_engine(SQLALCHEMY_DATABASE_URL)
    
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True
        )
        
        with context.begin_transaction():
            context.run_migrations()

# Загружаем конфиг alembic.ini
config = context.config
fileConfig(config.config_file_name)
run_migrations_online()