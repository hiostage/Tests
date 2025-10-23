from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, RedisDsn, AnyUrl
from typing import List
import yaml

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

    DATABASE_URL: str

    # Redis
    REDIS_URL: str = Field(default="redis://redis:6379/0")
    REDIS_PASSWORD: str = Field(..., env="REDIS_PASSWORD")

    # RabbitMQ
    RABBITMQ_USER: str
    RABBITMQ_PASS: str

    RABBITMQ_URL: str


    # Прокси для аутентификации
    AUTH_PROXY_URL: AnyUrl
    REQUEST_TIMEOUT: float = 5.0

    # Настройки Pydantic
    model_config = SettingsConfigDict(
        case_sensitive=True,
        extra="allow"  # Разрешает лишние переменные окружения
    )

def load_settings_from_yaml(path: str = "Config.yaml") -> Settings:
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    return Settings(**data)

settings = load_settings_from_yaml()



class TestSettings(BaseSettings):
    DATABASE_URL: str  
    REDIS_URL: str = Field(default="redis://test_redis:6379/0")  # Используем имя сервиса Redis в Docker Compose
    testing: bool
    db_host: str
    postgres_user: str
    postgres_password: str
    postgres_db: str
    rabbitmq_user: str
    rabbitmq_pass: str
    rabbitmq_url: str
    auth_proxy_url: str
    request_timeout: int
    allowed_origins: list[str]
    cors_allow_credentials: bool
    require_scopes: bool
    log_level: str
    log_format: str

    class Config:
        env_file = ".env.test"
        env_file_encoding = "utf-8"

# Создание экземпляра настроек
test_settings = TestSettings()