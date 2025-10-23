import aio_pika
import os
from aio_pika.abc import AbstractRobustConnection

rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
connection: AbstractRobustConnection = None

async def init_rabbitmq():
    global connection
    connection = await aio_pika.connect_robust(rabbitmq_url)

async def get_rabbitmq_connection() -> AbstractRobustConnection:
    if not connection:
        await init_rabbitmq()
    return connection

async def publish_message(queue_name: str, message: str):
    connection = await get_rabbitmq_connection()
    channel = await connection.channel()
    queue = await channel.declare_queue(queue_name, durable=True)
    await channel.default_exchange.publish(
        aio_pika.Message(body=message.encode()),
        routing_key=queue_name
    )