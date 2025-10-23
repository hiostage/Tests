import aio_pika
import asyncio
import json
from app.core.es_client import save_to_elasticsearch
import os

RABBITMQ_URL = f"amqp://user:password@{os.getenv('RABBITMQ_HOST', 'rabbitmq')}:5672/"



async def process_message(message: aio_pika.IncomingMessage):
    async with message.process():
        try:
            print(f"[*] Получено сообщение: {message.body.decode()}")  # Выводим само сообщение
            data = json.loads(message.body)
            await save_to_elasticsearch(data["index"], data["id"], data["body"])
            print(f"[*] Обработано сообщение: {data}")
        except Exception as e:
            print(f"[Ошибка] Не удалось обработать сообщение: {e}")


async def start_rabbitmq():
    while True:
        try:
            connection = await aio_pika.connect_robust(RABBITMQ_URL)
            channel = await connection.channel()

            # Объявляем exchange, если его нет
            exchange = await channel.declare_exchange("search_exchange", aio_pika.ExchangeType.DIRECT, durable=True)

            # Объявляем очередь и привязываем ее к exchange
            queue = await channel.declare_queue("search_updates", durable=True)
            await queue.bind(exchange, routing_key="search_updates")

            await queue.consume(process_message)
            print("[*] Ожидание сообщений...")

            await asyncio.Future()  # Бесконечное ожидание
        except Exception as e:
            print(f"[Ошибка] {e}. Повторное подключение через 5 секунд...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(start_rabbitmq())
