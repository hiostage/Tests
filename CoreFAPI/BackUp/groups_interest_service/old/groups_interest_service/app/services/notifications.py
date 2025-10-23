import pika
from app.config.settings import settings
import json

def send_notification(message: str, queue: str = "notifications"):
    """Отправка уведомления в RabbitMQ"""
    try:
        # Исправлено: добавлена закрывающая скобка для URLParameters
        connection = pika.BlockingConnection(
            pika.URLParameters(settings.RABBITMQ_URL)
        )
        channel = connection.channel()
        channel.queue_declare(queue=queue)
        channel.basic_publish(
            exchange="",
            routing_key=queue,
            body=json.dumps({"message": message})
        )
        connection.close()
    except pika.exceptions.AMQPConnectionError as e:
        print(f"Error connecting to RabbitMQ: {e}")
    except json.JSONEncodeError as e:
        print(f"Error encoding message: {e}")