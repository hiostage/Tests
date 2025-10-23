from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.chat import Chat
from app.schemas.chat import ChatCreate

async def create_chat(db: AsyncSession, chat_data: ChatCreate) -> Chat:
    """Создать новый чат."""
    new_chat = Chat(**chat_data.model_dump())
    db.add(new_chat)
    await db.commit()
    await db.refresh(new_chat)
    return new_chat

async def get_chat(db: AsyncSession, chat_id: int) -> Chat | None:
    """Получить чат по ID."""
    result = await db.execute(select(Chat).where(Chat.id == chat_id))
    return result.scalars().first()
