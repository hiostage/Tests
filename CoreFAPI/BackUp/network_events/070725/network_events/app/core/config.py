from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, RedisDsn, AnyUrl
from typing import List
import yaml

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
        case_sensitive=True,
        extra="allow"  # Разрешает лишние переменные окружения
    )

def load_settings_from_yaml(path: str = "config.yaml") -> Settings:
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
    return Settings(**data)


settings = load_settings_from_yaml()

