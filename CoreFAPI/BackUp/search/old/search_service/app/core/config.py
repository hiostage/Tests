import os
from dotenv import load_dotenv

load_dotenv()

ELASTICSEARCH_HOST = os.getenv("ELASTICSEARCH_HOST", "http://elasticsearch:9200")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://user:password@rabbitmq/")
