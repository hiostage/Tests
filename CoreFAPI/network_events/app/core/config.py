from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, RedisDsn, AnyUrl
from typing import List

class Settings(BaseSettings):

    DATABASE_URL: str  # будет прочитано напрямую из .env
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

