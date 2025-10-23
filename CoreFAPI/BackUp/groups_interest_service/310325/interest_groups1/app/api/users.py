from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.schemas.user import User, UserCreate
from app.services.user import get_user, get_users, create_user
from app.db.session import get_db
from app.utils.auth import get_current_user

router = APIRouter()

@router.get("/", response_model=List[User])
def read_users(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить список пользователей"""
    return get_users(db, skip=skip, limit=limit)

@router.get("/{user_id}", response_model=User)
def read_user(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить информацию о пользователе"""
    db_user = get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_new_user(
    user: UserCreate, 
    db: Session = Depends(get_db)
):
    """Создать нового пользователя (для интеграции с другим микросервисом)"""
    return create_user(db=db, user=user)