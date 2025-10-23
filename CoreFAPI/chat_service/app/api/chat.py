from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.chat import Chat
from app.db import get_db
from app.schemas.chat import ChatCreate, ChatResponse

router = APIRouter(prefix="/chats", tags=["Чаты"])

# Создать чат
@router.post("/", response_model=ChatResponse)
async def create_chat(chat_data: ChatCreate, db: AsyncSession = Depends(get_db)):
    new_chat = Chat(name=chat_data.name, is_group=chat_data.is_group)
    db.add(new_chat)
    await db.commit()
    await db.refresh(new_chat)
    return new_chat

# Получить список чатов
@router.get("/", response_model=list[ChatResponse])
async def get_chats(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Chat))
    return result.scalars().all()

# Получить чат по ID
@router.get("/{chat_id}", response_model=ChatResponse)
async def get_chat(chat_id: int, db: AsyncSession = Depends(get_db)):
    chat = await db.get(Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Чат не найден")
    return chat
