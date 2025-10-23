from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    POSTGRES_URL: str = "postgresql+asyncpg://admin:password@postgres:5432/groups_db"
    REDIS_URL: str = "redis://redis:6379"
    RABBITMQ_URL: str = "amqp://guest:guest@rabbitmq:5672"

    class Config:
        env_file = ".env"

settings = Settings()