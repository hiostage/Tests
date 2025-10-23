import aio_pika

async def handle_message(message: aio_pika.IncomingMessage):
    async with message.process():
        print("Received message:", message.body.decode())

async def start_consumer():
    connection = await aio_pika.connect_robust("amqp://guest:guest@localhost/")
    channel = await connection.channel()
    queue = await channel.declare_queue("events_queue", durable=True)
    await queue.consume(handle_message)
    print("Started RabbitMQ consumer...")
    return connection
