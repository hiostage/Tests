from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()  # Загружаем переменные окружения из .env

class Settings(BaseSettings):
    ELASTICSEARCH_URL: str = "http://elasticsearch:9200"
    REDIS_URL: str = "redis://192.168.1.118:6379"
    POSTGRES_USER: str = "user"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "search_db"
    POSTGRES_HOST: str = "192.168.1.114"
    POSTGRES_PORT: int = 5432
    MONGO_URL: str = "mongodb://192.168.1.113:27017"

    class Config:
        env_file = ".env"

settings = Settings()