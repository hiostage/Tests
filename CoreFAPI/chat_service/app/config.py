from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    CHAT_DB_URL: str
    USERS_DB_URL: str
    SECRET_KEY: str
    DEBUG: bool

    class Config:
        env_file = ".env"

settings = Settings()
