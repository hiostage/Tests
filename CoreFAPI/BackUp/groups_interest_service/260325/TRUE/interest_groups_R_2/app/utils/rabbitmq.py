import aio_pika
import os
from aio_pika.abc import AbstractRobustConnection
from typing import Optional
import logging
import asyncio

# Настройка логгера
logger = logging.getLogger(__name__)

# Глобальное соединение (лучше использовать dependency injection в реальном проекте)
connection: Optional[AbstractRobustConnection] = None

async def init_rabbitmq(max_retries: int = 3, retry_delay: float = 2.0):
    """
    Инициализация подключения к RabbitMQ с повторными попытками
    
    :param max_retries: Максимальное количество попыток подключения
    :param retry_delay: Задержка между попытками в секундах
    """
    global connection
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Connecting to RabbitMQ (attempt {attempt}/{max_retries})...")
            connection = await aio_pika.connect_robust(
                rabbitmq_url,
                timeout=5.0  # Таймаут подключения
            )
            logger.info("Successfully connected to RabbitMQ")
            return
        except Exception as e:
            logger.error(f"RabbitMQ connection failed: {str(e)}")
            if attempt == max_retries:
                raise
            await asyncio.sleep(retry_delay)

async def get_rabbitmq_connection() -> AbstractRobustConnection:
    """Получение активного подключения с ленивой инициализацией"""
    if connection is None or connection.is_closed:
        await init_rabbitmq()
    return connection

async def publish_message(
    queue_name: str,
    message: str,
    persistent: bool = True,
    priority: Optional[int] = None
) -> None:
    """
    Публикация сообщения в очередь RabbitMQ
    
    :param queue_name: Название очереди
    :param message: Сообщение (строка)
    :param persistent: Сохранять сообщение при перезапуске брокера
    :param priority: Приоритет сообщения (0-255)
    """
    try:
        connection = await get_rabbitmq_connection()
        
        async with connection.channel() as channel:
            # Подтверждение доставки
            await channel.set_qos(prefetch_count=1)
            
            queue = await channel.declare_queue(
                queue_name,
                durable=True,  # Очередь сохраняется при перезапуске
                arguments={
                    'x-max-priority': 10  # Поддержка приоритетов
                } if priority is not None else None
            )
            
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=message.encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT if persistent else None,
                    priority=priority
                ),
                routing_key=queue_name
            )
            
        logger.debug(f"Message published to queue '{queue_name}'")
        
    except Exception as e:
        logger.error(f"Failed to publish message: {str(e)}")
        raise