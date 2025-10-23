from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy import delete
from app.models.post import Post
from app.schemas.post import PostCreate, PostUpdate, PostWithAuthor
from fastapi import HTTPException, status
from typing import List, Optional
from app.utils.logger import logger
from datetime import datetime
from app.services.user import UserService
from app.utils.cache import cache
from functools import wraps
from app.utils.rabbitmq import RabbitMQManager

def handle_db_errors(func):
    """Декоратор для обработки ошибок БД"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Database operation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database operation failed"
            )
    return wrapper


class PostService:
    @staticmethod
    @handle_db_errors
    async def get_post(db: AsyncSession, post_id: int) -> Optional[PostWithAuthor]:
        """Получение поста с информацией об авторе"""
        result = await db.execute(
            select(Post).options(joinedload(Post.author)).filter(Post.id == post_id)
        )
        post = result.scalars().first()
        return PostWithAuthor.from_orm(post) if post else None

    @staticmethod
    @cache.cached(ttl=60, key_prefix="posts_list")
    @handle_db_errors
    async def get_posts(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[PostWithAuthor]:
        """Получение списка постов с пагинацией"""
        result = await db.execute(
            select(Post).options(joinedload(Post.author)).offset(skip).limit(limit)
        )
        return [PostWithAuthor.from_orm(post) for post in result.scalars().all()]

    @staticmethod
    @cache.cached(ttl=60, key_prefix="group_posts")
    @handle_db_errors
    async def get_posts_by_group(
        db: AsyncSession,
        group_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[PostWithAuthor]:
        """Получение постов группы с пагинацией"""
        result = await db.execute(
            select(Post).options(joinedload(Post.author)).filter(Post.group_id == group_id).offset(skip).limit(limit)
        )
        return [PostWithAuthor.from_orm(post) for post in result.scalars().all()]

    @staticmethod
    @handle_db_errors
    async def create_post(
        db: AsyncSession,
        post_data: PostCreate,
        author_id: int
    ) -> PostWithAuthor:
        """Создание нового поста с проверкой автора"""
        
        # Получаем автора из базы данных по его ID
        author = await UserService.get_local_user(db, author_id)
        
        if not author:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Author not found"
            )
        
        # Создаем новый пост
        db_post = Post(
            **post_data.dict(),
            author_id=author_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Добавляем пост в базу данных и сохраняем
        db.add(db_post)
        await db.commit()
        await db.refresh(db_post)
        
        await RabbitMQManager.publish_event(
            event_type="group.post_created",
            payload={
                "group_id": db_post.group_id,
                "post_id": db_post.id,
                "author_id": author_id,
                "title": db_post.title,
                "created_at": db_post.created_at.isoformat()
            },
            routing_key="event.new_post"
)

        
        # Очищаем кэш, связанный с группой постов
        await cache.delete(f"group_posts:{db_post.group_id}")
        
        # Возвращаем созданный пост с автором
        return PostWithAuthor.from_orm(db_post)

    @staticmethod
    @handle_db_errors
    async def update_post(
        db: AsyncSession,
        post_id: int,
        post_data: PostUpdate
    ) -> PostWithAuthor:
        """Обновление поста"""
        result = await db.execute(select(Post).filter(Post.id == post_id))
        db_post = result.scalars().first()
        if not db_post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )
        
        update_data = post_data.dict(exclude_unset=True)
        for field in update_data:
            setattr(db_post, field, update_data[field])
        
        db_post.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(db_post)
        
        await cache.delete("posts_list")
        await cache.delete(f"group_posts:{db_post.group_id}")
        
        return PostWithAuthor.from_orm(db_post)
    
    
    @staticmethod
    async def get_post_by_id(db: AsyncSession, post_id: int):
        result = await db.execute(select(Post).filter(Post.id == post_id))
        return result.scalar_one_or_none()


    @staticmethod
    @handle_db_errors
    async def delete_post(db: AsyncSession, post_id: int) -> PostWithAuthor:
        """Удаление поста"""
        result = await db.execute(select(Post).filter(Post.id == post_id))
        db_post = result.scalars().first()
        if not db_post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )

        group_id = db_post.group_id

        await db.execute(delete(Post).where(Post.id == db_post.id))
        await db.commit()

        await cache.delete("posts_list")
        await cache.delete(f"group_posts:{group_id}")

        return PostWithAuthor.from_orm(db_post)
