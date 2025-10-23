from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.message import Message
from app.schemas.message import MessageCreate

async def create_message(db: AsyncSession, message_data: MessageCreate) -> Message:
    """Отправить сообщение в чат."""
    new_message = Message(**message_data.model_dump())
    db.add(new_message)
    await db.commit()
    await db.refresh(new_message)
    return new_message

async def get_messages(db: AsyncSession, chat_id: int, limit: int = 50):
    """Получить последние сообщения из чата."""
    result = await db.execute(select(Message).where(Message.chat_id == chat_id).order_by(Message.created_at.desc()).limit(limit))
    return result.scalars().all()
