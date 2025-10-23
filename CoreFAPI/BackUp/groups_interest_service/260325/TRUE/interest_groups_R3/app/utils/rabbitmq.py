import aio_pika
import os
from aio_pika.abc import AbstractRobustConnection
from typing import Optional
import logging
import asyncio

logger = logging.getLogger(__name__)

class RabbitMQManager:
    _connection: Optional[AbstractRobustConnection] = None
    _lock = asyncio.Lock()  # Защита от гонки условий при подключении

    @classmethod
    async def get_connection(cls) -> AbstractRobustConnection:
        """Получение или создание соединения с thread-safe инициализацией"""
        if cls._connection is None or cls._connection.is_closed:
            async with cls._lock:
                if cls._connection is None or cls._connection.is_closed:  # Double-check
                    await cls._connect()
        return cls._connection

    @classmethod
    async def _connect(cls, max_retries: int = 5, initial_delay: float = 2.0):
        """Улучшенное подключение с экспоненциальной задержкой"""
        url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
        delay = initial_delay
        
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Connecting to RabbitMQ (attempt {attempt}/{max_retries})")
                cls._connection = await aio_pika.connect_robust(
                    url,
                    timeout=10.0,  # Увеличенный таймаут
                    client_properties={
                        "connection_name": "interest_groups_service"  # Для идентификации в админке
                    }
                )
                logger.info("RabbitMQ connection established")
                return
            except Exception as e:
                logger.error(f"Connection failed: {str(e)}")
                if attempt == max_retries:
                    raise
                
                await asyncio.sleep(delay)
                delay = min(delay * 1.5, 10.0)  # Экспоненциальный backoff с ограничением

    @classmethod
    async def publish(
        cls,
        queue_name: str,
        message: str,
        persistent: bool = True,
        priority: Optional[int] = None,
        expiration: Optional[int] = None
    ) -> None:
        """Безопасная публикация сообщения с обработкой ошибок"""
        try:
            connection = await cls.get_connection()
            
            async with connection.channel() as channel:
                await channel.declare_queue(
                    queue_name,
                    durable=True,
                    arguments={
                        'x-max-priority': 10,
                        'x-message-ttl': expiration if expiration else None
                    }
                )
                
                await channel.default_exchange.publish(
                    aio_pika.Message(
                        body=message.encode(),
                        delivery_mode=aio_pika.DeliveryMode.PERSISTENT if persistent else None,
                        priority=priority,
                        expiration=str(expiration) if expiration else None
                    ),
                    routing_key=queue_name
                )
                
            logger.info(f"Message published to '{queue_name}'")
            
        except aio_pika.exceptions.ChannelClosed as e:
            logger.error(f"Channel error: {e}. Reconnecting...")
            await cls._reconnect()
            await cls.publish(queue_name, message, persistent, priority, expiration)
        except Exception as e:
            logger.error(f"Critical publish error: {e}")
            raise

    @classmethod
    async def _reconnect(cls):
        """Явное переподключение"""
        if cls._connection:
            await cls._connection.close()
        cls._connection = None
        await cls._connect()

# Функции для обратной совместимости
async def init_rabbitmq():
    """Инициализация для startup event"""
    await RabbitMQManager._connect()

async def publish_message(queue_name: str, message: str, **kwargs):
    """Обертка для старого интерфейса"""
    await RabbitMQManager.publish(queue_name, message, **kwargs)