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
    REQUEST_TIMEOUT: float = 5.0

    # Настройки Pydantic
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"  # Разрешает лишние переменные окружения
    )

settings = Settings()



class TestSettings(BaseSettings):
    DATABASE_URL: str  # Поменяй на DATABASE_URL, чтобы оно совпало с переменной в .env
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
    auth_proxy_token: str
    auth_proxy_fallback_token: str
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