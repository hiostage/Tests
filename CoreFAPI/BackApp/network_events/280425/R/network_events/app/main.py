from fastapi import FastAPI
from app.api import events, participants
from app.db.database import create_db_and_tables
from contextlib import asynccontextmanager
from app.utils.rabbitmq import rabbitmq_publisher
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,  # Уровень логирования: INFO, DEBUG, WARNING, ERROR
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Создаём приложение с lifespan
def create_app() -> FastAPI:
    app = FastAPI(
        title="Сетевые мероприятия",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    
    # Подключаем роутеры
    app.include_router(participants.router)
    app.include_router(events.router)
    app.include_router(participants.router, prefix="/participants", tags=["participants"])
    
    return app

# Используем lifespan для подключения к RabbitMQ
@asynccontextmanager
async def lifespan(app: FastAPI):
    await rabbitmq_publisher.connect()  # Подключение к RabbitMQ
    yield
    await rabbitmq_publisher.close()    # Закрытие подключения

# Создаём экземпляр приложения с lifespan
app = create_app()

# Указываем lifespan для приложения
app.state.lifespan = lifespan

# Добавляем событие для старта и остановки приложения
@app.on_event("startup")
async def on_startup():
    await create_db_and_tables()
    # Убедитесь, что RabbitMQ подключён перед тем, как приложение начнёт принимать запросы.
    await rabbitmq_publisher.connect()
