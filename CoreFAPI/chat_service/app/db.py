from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Движок для БД сообщений
chat_engine = create_async_engine(settings.CHAT_DB_URL, echo=True, future=True)

# Движок для БД пользователей (читаем только)
users_engine = create_async_engine(settings.USERS_DB_URL, echo=True, future=True)

# Фабрика сессий для БД чатов
ChatSessionLocal = sessionmaker(
    bind=chat_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Фабрика сессий для БД пользователей (только чтение)
UsersSessionLocal = sessionmaker(
    bind=users_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Dependency для работы с БД чатов
async def get_chat_db():
    async with ChatSessionLocal() as session:
        yield session

# Dependency для работы с БД пользователей
async def get_users_db():
    async with UsersSessionLocal() as session:
        yield session
