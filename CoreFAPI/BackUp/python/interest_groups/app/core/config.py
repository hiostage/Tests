from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, RedisDsn, AnyUrl
from typing import List
import yaml

class Settings(BaseSettings):
    # Базовые настройки
    POSTGRES_HOST: str = "192.168.1.114"
    REDIS_HOST: str = "192.168.1.118"
    RABBITMQ_HOST: str = "192.168.1.117"

    POSTGRES_PORT: int = 5432
    RABBITMQ_PORT: int = 5672
    REDIS_PORT: int = 6379

    # Настройки безопасности
    ALLOWED_ORIGINS: List[str] = Field(default=["http://localhost:3000"], description="Разрешенные CORS-источники")
    CORS_ALLOW_CREDENTIALS: bool = True

    # Настройки БД
    POSTGRES_USER: str = "interest_groups"
    POSTGRES_PASSWORD: str = "interest_groups"
    POSTGRES_DB: str = "interest_groups"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Redis
    REDIS_URL: RedisDsn = Field(default="redis://192.168.1.118:6379/0")
    REDIS_PASSWORD: str = "redis"

    # RabbitMQ
    RABBITMQ_USER: str = "interest_groups"
    RABBITMQ_PASS: str = "interest_groups"

    @property
    def RABBITMQ_URL(self) -> str:
        return f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASS}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/"

    # Прокси для аутентификации
    AUTH_PROXY_URL: AnyUrl = "http://registr:8010"
    REQUEST_TIMEOUT: float = 5.0

    # Настройки Pydantic
    model_config = SettingsConfigDict(
        case_sensitive=True,
        extra="allow"  # Разрешает лишние переменные
    )

def load_settings_from_yaml(path: str = "config.yaml") -> Settings:
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    return Settings(**data)

settings = load_settings_from_yaml()
