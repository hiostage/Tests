from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "postgresql+asyncpg://user:password@db:5432/db"

Base = declarative_base()

engine = create_async_engine(DATABASE_URL, future=True, echo=True)

async_session_maker = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit = False
)

async def get_db():
    async with async_session_maker() as session:
        yield session

async def create_db_and_table():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

