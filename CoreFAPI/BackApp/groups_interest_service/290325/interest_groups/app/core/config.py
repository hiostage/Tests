from pydantic import BaseSettings, HttpUrl, PostgresDsn, RedisDsn, SecretStr, validator
from typing import List, Optional

class Settings(BaseSettings):
    # Настройки внешнего сервиса аутентификации
    AUTH_SERVICE_URL: HttpUrl = "http://auth-service/api/v1"
    AUTH_SERVICE_TOKEN: SecretStr = "your-service-token"
    AUTH_USER_CACHE_TTL: int = 3600  # 1 hour in seconds
    
    # Настройки БД
    POSTGRES_USER: str
    POSTGRES_PASSWORD: SecretStr
    POSTGRES_DB: str
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: str = "5432"
    
    @property
    def database_url(self) -> PostgresDsn:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD.get_secret_value()}" \
               f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # Настройки Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: SecretStr = SecretStr("")
    REDIS_CACHE_TTL: int = 300  # 5 minutes
    
    @property
    def redis_url(self) -> str:
        password = f":{self.REDIS_PASSWORD.get_secret_value()}@" if self.REDIS_PASSWORD else ""
        return f"redis://{password}{self.REDIS_HOST}:{self.REDIS_PORT}/0"
    
    # Настройки приложения
    DEBUG: bool = False
    PROJECT_NAME: str = "Interest Groups Service"
    REQUEST_TIMEOUT: int = 10  # seconds
    
    # Настройки безопасности
    JWT_PUBLIC_KEY: Optional[SecretStr] = None
    CORS_ORIGINS: List[str] = ["*"]
    
    # Настройки логирования
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

class TestSettings(Settings):
    POSTGRES_DB: str = "test_db"
    REDIS_DB: int = 1
    
    class Config:
        env_prefix = "TEST_"

settings = Settings()