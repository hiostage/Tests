# app/utils/rabbitmq.py
import aio_pika
import os
from aio_pika.abc import AbstractRobustConnection
from typing import Optional, Dict, Any
import asyncio
from functools import wraps
from contextlib import asynccontextmanager
from datetime import datetime
import json
from app.utils.logger import logger
from app.core.config import settings

class RabbitMQManager:
    _connection: Optional[AbstractRobustConnection] = None
    _lock = asyncio.Lock()
    
    # Конфигурация из переменных окружения
    RABBITMQ_URL = settings.RABBITMQ_URL
    RABBITMQ_TIMEOUT = settings.RABBITMQ_TIMEOUT  # Явное преобразование в float
    MAX_RETRIES = int("5")
    INITIAL_DELAY = int("2")

    @classmethod
    async def get_connection(cls) -> AbstractRobustConnection:
        """Получение активного соединения с автоматическим восстановлением"""
        if cls._is_connection_broken():
            async with cls._lock:
                if cls._is_connection_broken():
                    await cls._connect_with_retry()
        return cls._connection

    @classmethod
    def _is_connection_broken(cls) -> bool:
        return cls._connection is None or cls._connection.is_closed

    @classmethod
    async def _connect_with_retry(cls):
        """Подключение с экспоненциальной задержкой"""
        delay = cls.INITIAL_DELAY
        last_exception = None
        
        for attempt in range(1, cls.MAX_RETRIES + 1):
            try:
                logger.info(f"Connecting to RabbitMQ (attempt {attempt}, timeout: {cls.RABBITMQ_TIMEOUT}s)")
                cls._connection = await aio_pika.connect_robust(
                    cls.RABBITMQ_URL,
                    timeout=cls.RABBITMQ_TIMEOUT,  # Передаем float напрямую
                    client_properties={
                        "connection_name": "interest_groups_service",
                        "service": "interest_groups"
                    }
                )
                logger.info("RabbitMQ connection established successfully")
                return
            except Exception as e:
                last_exception = e
                logger.warning(f"Connection attempt {attempt} failed: {str(e)}")
                if attempt < cls.MAX_RETRIES:
                    await asyncio.sleep(delay)
                    delay = min(delay * 1.5, 10.0)  # Явно указываем float
                else:
                    logger.error("Max connection attempts reached, unable to connect to RabbitMQ.")
                    
        logger.error(f"Failed to connect to RabbitMQ after {cls.MAX_RETRIES} attempts.")
        raise last_exception or Exception("Failed to connect to RabbitMQ")

    @classmethod
    @asynccontextmanager
    async def get_channel(cls):
        """Контекстный менеджер для работы с каналом"""
        connection = await cls.get_connection()
        channel = await connection.channel()
        logger.debug("RabbitMQ channel created.")
        try:
            yield channel
        finally:
            await channel.close()
            logger.debug("RabbitMQ channel closed.")

    @classmethod
    async def publish_event(
        cls,
        event_type: str,
        payload: Dict[str, Any],
        routing_key: str = None,
        persistent: bool = True
    ):
        """Публикация события в RabbitMQ"""
        try:
            async with cls.get_channel() as channel:
                exchange = await channel.declare_exchange(
                    "interest_groups_events",
                    type=aio_pika.ExchangeType.TOPIC,
                    durable=True
                )
                
                message = aio_pika.Message(
                    body=json.dumps({
                        "event_type": event_type,
                        "payload": payload,
                        "timestamp": datetime.utcnow().isoformat()
                    }).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT if persistent else None,
                    content_type="application/json"
                )
                
                # Публикуем в очередь, привязанную к нужному event_type
                await exchange.publish(
                    message,
                    routing_key=routing_key or f"event.{event_type}",
                    mandatory=True
                )
                logger.info(f"Event '{event_type}' published successfully.")
                
        except Exception as e:
            logger.error(f"Failed to publish event '{event_type}': {str(e)}")
            raise

    @classmethod
    async def setup_event_consumers(cls):
        """Настройка потребителей событий"""
        # Этот метод вызывается только в другом сервисе, который должен обрабатывать события
        connection = await cls.get_connection()
        channel = await connection.channel()
        logger.info("Setting up event consumers...")
        
        # Объявляем общий exchange
        exchange = await channel.declare_exchange(
            "interest_groups_events",
            type=aio_pika.ExchangeType.TOPIC,
            durable=True
        )
        
        # Очередь для уведомлений
        notifications_queue = await channel.declare_queue(
            "interest_groups_notifications",
            durable=True,
            arguments={
                "x-message-ttl": 86400000,  # 24 часа
                "x-max-length": 10000
            }
        )
        
        # Биндим к событиям
        await notifications_queue.bind(exchange, routing_key="event.*")
        logger.info("Event consumer setup complete, binding done.")
        
        # Запускаем consumer в фоне
        # asyncio.create_task(cls._consume_notifications(notifications_queue))

    @classmethod
    async def _consume_notifications(cls, queue):
        """Обработчик уведомлений"""
        logger.info("Starting to consume notifications...")
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                try:
                    async with message.process():
                        event = json.loads(message.body.decode())
                        logger.info(f"Processing event: {event['event_type']}")
                        
                        # Здесь можно добавить логику обработки событий
                        # Например, отправка уведомлений пользователям
                        
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")

# Инициализация при старте приложения
async def init_rabbitmq():
    """Инициализация RabbitMQ при запуске сервиса"""
    try:
        logger.info("Initializing RabbitMQ connection...")
        await RabbitMQManager._connect_with_retry()
        await RabbitMQManager.setup_event_consumers()
        logger.info("RabbitMQ initialization successful.")
    except Exception as e:
        logger.error(f"Failed to initialize RabbitMQ: {str(e)}")
        raise
