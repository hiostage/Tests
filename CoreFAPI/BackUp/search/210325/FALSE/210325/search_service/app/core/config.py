from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Загружаем переменные окружения из .env
load_dotenv()

class Settings(BaseSettings):
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    REDIS_URL: str = "redis://localhost:6379"
    USER_SERVICE_URL: str = "http://user-service:8000"
    PROJECT_SERVICE_URL: str = "http://project-service:8000"
    JOB_SERVICE_URL: str = "http://job-service:8000"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    DEBUG: bool = True

    class Config:
        env_file = ".env"

settings = Settings()