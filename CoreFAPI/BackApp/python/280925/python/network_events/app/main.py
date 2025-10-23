from fastapi import FastAPI
from app.api import events, participants
from app.db.database import create_db_and_tables
from contextlib import asynccontextmanager
from app.utils.rabbitmq import rabbitmq_publisher
import logging
from logging.handlers import RotatingFileHandler
import os
from app.utils.cache import init_cache, close_cache

# Настройка логирования
log_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
log_dir = "/app/logs" 
log_file = os.path.join(log_dir, "app.log")

# Создаем обработчик для файла
file_handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5)  # 10 MB, до 5 резервных копий
file_handler.setFormatter(log_formatter)

# Добавляем обработчик для консоли
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

# Основная настройка логирования
logging.basicConfig(
    level=logging.INFO,  # Уровень логирования: INFO, DEBUG, WARNING, ERROR
    handlers=[console_handler, file_handler]  # Выводим как в консоль, так и в файл
)

logger = logging.getLogger("app")

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
    await close_cache()

# Создаём экземпляр приложения с lifespan
app = create_app()

# Указываем lifespan для приложения
app.state.lifespan = lifespan

# Добавляем событие для старта и остановки приложения
@app.on_event("startup")
async def on_startup():
    await init_cache()
    await create_db_and_tables()
    # Убедитесь, что RabbitMQ подключён перед тем, как приложение начнёт принимать запросы.
    await rabbitmq_publisher.connect()
