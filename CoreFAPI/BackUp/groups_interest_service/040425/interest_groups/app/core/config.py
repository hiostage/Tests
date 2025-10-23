from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, RedisDsn, AnyUrl
from typing import List

class Settings(BaseSettings):
    # Базовые настройки
    POSTGRES_HOST: str = "db"
    REDIS_HOST: str = "redis"
    RABBITMQ_HOST: str = "rabbitmq"

    POSTGRES_PORT: int = 5432
    RABBITMQ_PORT: int = 5672
    REDIS_PORT: int = 6379

    # Настройки безопасности
    ALLOWED_ORIGINS: List[str] = Field(default=["http://localhost:3000"], description="Разрешенные CORS-источники")
    CORS_ALLOW_CREDENTIALS: bool = True

    # Настройки БД
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str = "interest_groups"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Redis
    REDIS_URL: RedisDsn = Field(default="redis://redis:6379/0")
    REDIS_CACHE_TTL: int = 300

    # RabbitMQ
    RABBITMQ_USER: str
    RABBITMQ_PASS: str

    @property
    def RABBITMQ_URL(self) -> str:
        return f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASS}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/"

    # Прокси для аутентификации
    AUTH_PROXY_URL: AnyUrl

    # Настройки Pydantic
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"  # Разрешает лишние переменные окружения
    )

settings = Settings()
