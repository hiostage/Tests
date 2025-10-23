from unittest.mock import AsyncMock, MagicMock
from fastapi import FastAPI

def apply_mocks(app: FastAPI):
    # Мокируем Redis
    app.state.redis = AsyncMock()
    app.state.redis.get.return_value = None
    app.state.redis.set.return_value = True
    
    # Мокируем RabbitMQ
    app.state.rabbit_channel = AsyncMock()
    app.state.rabbit_connection = MagicMock()
    app.state.rabbit_connection.channel.return_value = app.state.rabbit_channel