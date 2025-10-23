#!/bin/sh
# entrypoint.sh

# Выполнить миграции
alembic upgrade head

# Перейти в директорию с приложением, если не получилось — завершить с ошибкой
cd app || exit 1

# Запустить приложение
exec uvicorn main:app --host 0.0.0.0 --port 8000
