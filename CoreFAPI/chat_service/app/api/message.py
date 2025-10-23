from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.chat import Message
from app.db import get_chat_db, get_users_db
from app.schemas.message import MessageCreate, MessageResponse

router = APIRouter(prefix="/messages", tags=["Сообщения"])

# Функция для проверки пользователя в общей БД
async def get_user_by_id(user_id: int, db: AsyncSession):
    result = await db.execute(select(User).where(User.id == user_id))  # User - это модель из общей БД
    user = result.scalar()
    return user

# Отправить сообщение
@router.post("/", response_model=MessageResponse)
async def send_message(
    message_data: MessageCreate,
    chat_db: AsyncSession = Depends(get_chat_db),
    users_db: AsyncSession = Depends(get_users_db)  # Подключение к БД пользователей
):
    # Проверяем, существует ли пользователь
    user = await get_user_by_id(message_data.sender_id, users_db)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Создаем сообщение
    new_message = Message(
        chat_id=message_data.chat_id,
        sender_id=message_data.sender_id,
        content=message_data.content
    )
    chat_db.add(new_message)
    await chat_db.commit()
    await chat_db.refresh(new_message)
    
    return new_message
