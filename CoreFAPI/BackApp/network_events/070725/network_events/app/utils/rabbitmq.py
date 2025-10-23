import aio_pika
from aio_pika import Message
import json
import logging
from app.core.config import settings

logger = logging.getLogger("app")
class RabbitMQPublisher:
    def __init__(self, url: str):
        self.url = url
        self.connection = None
        self.channel = None

    async def connect(self):
        logger.info(f"Подключаемся к RabbitMQ по адресу {self.url}...")
        self.connection = await aio_pika.connect_robust(self.url)
        self.channel = await self.connection.channel()
        
        # Создаём очередь при подключении
        await self.channel.declare_queue("event_participants", durable=True)
        await self.channel.declare_queue("event_updates", durable=True)
        
        logger.info("Успешное подключение к RabbitMQ и создание очередей.")

    async def publish(self, queue_name: str, message: dict):
        if not self.channel:
            logger.error("RabbitMQ channel не инициализирован. Необходимо вызвать connect() перед использованием.")
            raise Exception("RabbitMQ channel not initialized. Call connect() first.")

        logger.info(f"Отправка сообщения в очередь '{queue_name}' с данными: {message}")
        
        await self.channel.default_exchange.publish(
            Message(
                body=json.dumps(message).encode(),
                content_type="application/json",
            ),
            routing_key=queue_name,
        )

        logger.info(f"Сообщение успешно отправлено в очередь '{queue_name}'.")

    async def close(self):
        if self.connection:
            logger.info("Закрываем соединение с RabbitMQ...")
            await self.connection.close()
            logger.info("Соединение с RabbitMQ закрыто.")


rabbitmq_publisher = RabbitMQPublisher(settings.RABBITMQ_URL)
