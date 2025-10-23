#!/bin/bash

# Apply database migrations
echo "Apply database migrations"
alembic upgrade head

# Start server
echo "Starting server"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

#!/bin/bash
echo "Waiting for RabbitMQ..."
sleep 15  # Увеличьте при необходимости
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000