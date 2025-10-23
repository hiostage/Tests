import aio_pika
import os
from aio_pika.abc import AbstractRobustConnection
from typing import Optional, Dict, Any
import logging
import asyncio
from functools import wraps
from contextlib import asynccontextmanager
from datetime import datetime
import json
import signal

logger = logging.getLogger("interest_groups.rabbitmq")

class RabbitMQManager:
    _connection: Optional[AbstractRobustConnection] = None
    _lock = asyncio.Lock()
    
    RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
    RABBITMQ_TIMEOUT = float(os.getenv("RABBITMQ_TIMEOUT", "10"))
    MAX_RETRIES = int(os.getenv("RABBITMQ_MAX_RETRIES", "5"))
    INITIAL_DELAY = float(os.getenv("RABBITMQ_INITIAL_DELAY", "2"))

    @classmethod
    async def get_connection(cls) -> AbstractRobustConnection:
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
        delay = cls.INITIAL_DELAY
        last_exception = None
        
        for attempt in range(1, cls.MAX_RETRIES + 1):
            try:
                logger.info(f"Connecting to RabbitMQ (attempt {attempt}, timeout: {cls.RABBITMQ_TIMEOUT}s)")
                cls._connection = await aio_pika.connect_robust(
                    cls.RABBITMQ_URL,
                    timeout=cls.RABBITMQ_TIMEOUT,
                    client_properties={"connection_name": "interest_groups_service", "service": "interest_groups"}
                )
                logger.info("RabbitMQ connection established")
                return
            except Exception as e:
                last_exception = e
                logger.warning(f"Connection failed: {str(e)}")
                if attempt < cls.MAX_RETRIES:
                    await asyncio.sleep(delay)
                    delay = min(delay * 1.5, 10.0)

        logger.error("Max connection attempts reached")
        raise last_exception or Exception("Failed to connect to RabbitMQ")

    @classmethod
    @asynccontextmanager
    async def get_channel(cls):
        connection = await cls.get_connection()
        channel = await connection.channel()
        try:
            yield channel
        finally:
            await channel.close()

    @classmethod
    async def publish_event(cls, event_type: str, payload: Dict[str, Any], routing_key: str = None, persistent: bool = True):
        try:
            async with cls.get_channel() as channel:
                exchange = await channel.declare_exchange("interest_groups_events", type=aio_pika.ExchangeType.TOPIC, durable=True)
                
                message = aio_pika.Message(
                    body=json.dumps({
                        "event_type": event_type,
                        "payload": payload,
                        "timestamp": datetime.utcnow().isoformat()
                    }).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT if persistent else None,
                    content_type="application/json"
                )
                
                await exchange.publish(message, routing_key=routing_key or f"event.{event_type}")
            logger.debug(f"Published event: {event_type}")
        except Exception as e:
            logger.error(f"Failed to publish event: {str(e)}")
            raise

    @classmethod
    async def setup_event_consumers(cls):
        connection = await cls.get_connection()
        channel = await connection.channel()
        
        exchange = await channel.declare_exchange("interest_groups_events", type=aio_pika.ExchangeType.TOPIC, durable=True)
        
        notifications_queue = await channel.declare_queue(
            "interest_groups_notifications",
            durable=True,
            arguments={"x-message-ttl": 86400000, "x-max-length": 10000}
        )
        
        await notifications_queue.bind(exchange, routing_key="event.*")
        
        await cls._consume_notifications(notifications_queue)

    @classmethod
    async def _consume_notifications(cls, queue):
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                try:
                    async with message.process():
                        event = json.loads(message.body.decode())
                        logger.info(f"Processing event: {event['event_type']}")
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")

# Инициализация при старте приложения
async def init_rabbitmq():
    try:
        await RabbitMQManager._connect_with_retry()
        await RabbitMQManager.setup_event_consumers()
    except Exception as e:
        logger.error(f"Failed to initialize RabbitMQ: {str(e)}")
        raise

async def main():
    loop = asyncio.get_event_loop()

    def signal_handler(signum, frame):
        logger.info(f"Signal {signum} received, stopping...")
        loop.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    await init_rabbitmq()
    await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(main())
