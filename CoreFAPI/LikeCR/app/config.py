from pydantic import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL = "postgresql+asyncpg://user:password@likecr-postgres/dbname"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings(_env_file=None)  # <- Указываем, что .env не нужен
