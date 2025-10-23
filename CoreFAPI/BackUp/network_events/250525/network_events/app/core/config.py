from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, RedisDsn, AnyUrl
from typing import List

class Settings(BaseSettings):

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Redis
    REDIS_URL: RedisDsn = Field(default="redis://redis:6379/0")

    @property
    def RABBITMQ_URL(self) -> str:
        return f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASS}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/"

    # Прокси для аутентификации
    AUTH_PROXY_URL: AnyUrl
    REQUEST_TIMEOUT: float = 5.0

    # Настройки Pydantic
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"  # Разрешает лишние переменные окружения
    )

settings = Settings()

