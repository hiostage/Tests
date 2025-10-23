import aio_pika
from aio_pika import Message
import json

class RabbitMQPublisher:
    def __init__(self, url: str):
        self.url = url
        self.connection = None
        self.channel = None

    async def connect(self):
        self.connection = await aio_pika.connect_robust(self.url)
        self.channel = await self.connection.channel()

        # Создаём очередь при подключении
        await self.channel.declare_queue("event_participants", durable=True)
        await self.channel.declare_queue("event_updates", durable=True)

    async def publish(self, queue_name: str, message: dict):
        if not self.channel:
            raise Exception("RabbitMQ channel not initialized. Call connect() first.")

        await self.channel.default_exchange.publish(
            Message(
                body=json.dumps(message).encode(),
                content_type="application/json",
            ),
            routing_key=queue_name,
        )

    async def close(self):
        if self.connection:
            await self.connection.close()


rabbitmq_publisher = RabbitMQPublisher("amqp://guest:guest@rabbitmq:5672/")