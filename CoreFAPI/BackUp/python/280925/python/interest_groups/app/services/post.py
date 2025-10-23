from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy import delete
from app.models.post import Post
from app.schemas.post import PostCreate, PostUpdate, PostWithAuthor
from typing import List, Optional
from app.utils.logger import logger
from datetime import datetime
from app.services.user import UserService
from app.utils.cache import cache
from app.utils.rabbitmq import RabbitMQManager
from app.exceptions.errors import PostNotFound, GroupNotFound, UserNotMemberThisGroup, AuthorNotFound, CreatorOnly
from app.models.group import group_members
from app.exceptions.error_handlers import handler_decorator

EXCEPTION_MAP = {
    "PostNotFound": PostNotFound,
    "GroupNotFound": GroupNotFound,
    "UserNotMemberThisGroup": UserNotMemberThisGroup,
    "CreatorOnly": CreatorOnly
}

class PostService():
    def __init__(self, db: AsyncSession, current_user):
        self.db = db
        self.current_user = current_user

    @handler_decorator
    async def get_post(self, post_id: int) -> Optional[PostWithAuthor]:
        """Получение поста с информацией об авторе"""
        logger.debug(f"Fetching post with id: {post_id}")

        result = await self.db.execute(
            select(Post).options(joinedload(Post.author)).filter(Post.id == post_id)
        )
        post = result.scalars().first()
        if not post:
            logger.warning(f"Post {post_id} not found")
            await self.handle_error(exception_cls=PostNotFound)

        logger.info(f"Post {post_id} found with author {post.author.username}")
        return PostWithAuthor.from_orm(post)

    @cache.cached(ttl=60, key_prefix="posts_list")
    @handler_decorator
    async def get_posts(self, skip: int = 0, limit: int = 100) -> List[PostWithAuthor]:
        """Получение списка постов с пагинацией"""
        logger.debug(f"Fetching posts with skip={skip}, limit={limit}")
        result = await self.db.execute(select(Post).options(joinedload(Post.author), joinedload(Post.group)).offset(skip).limit(limit))
        raw_posts = result.scalars().all()
        posts = []

        for post in raw_posts:
            try:
                posts.append(PostWithAuthor.from_orm(post))
            except ValueError as e:
                logger.warning(f"Post ID {getattr(post, 'id', 'unknown')} skipped: {e}")

        logger.info(f"Fetched {len(posts)} valid posts out of {len(raw_posts)}")
        return posts

    @cache.cached(ttl=60, key_prefix="group_posts")
    @handler_decorator
    async def get_posts_by_group(self, group_id: int, skip: int = 0, limit: int = 100) -> List[PostWithAuthor]:
        """Получение постов группы с пагинацией"""
        await self.get_group_by_id(group_id)

        logger.debug(f"Fetching posts for group {group_id} with skip={skip}, limit={limit}")
        result = await self.db.execute(
            select(Post).options(joinedload(Post.author)).filter(Post.group_id == group_id).offset(skip).limit(limit)
        )
        posts = [PostWithAuthor.from_orm(post) for post in result.scalars().all()]
        logger.info(f"Fetched {len(posts)} posts for group {group_id}")
        return posts

    @handler_decorator
    async def create_post(self, post_data: PostCreate) -> PostWithAuthor:
        """Создание нового поста с проверкой автора"""
        logger.debug(f"Creating post with title: {post_data.title} by author_id: {self.current_user.id}")
        
        await self.get_group_by_id(post_data.group_id)

        if not await self.is_group_member(self.current_user.id, post_data.group_id):
            logger.debug("User not member")
            await self.handle_error(exception_cls=UserNotMemberThisGroup)

        # Создаем новый пост
        db_post = Post(
            **post_data.dict(),
            author_id=self.current_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Добавляем пост в базу данных и сохраняем
        self.db.add(db_post)
        await self.db.commit()
        await self.db.refresh(db_post)
        
        logger.info(f"Post {db_post.id} created by {self.current_user.username}")

        # Публикуем событие
        await RabbitMQManager.publish_event(
            event_type="group.post_created",
            payload={
                "group_id": db_post.group_id,
                "post_id": db_post.id,
                "author_id": self.current_user.id,
                "title": db_post.title,
                "created_at": db_post.created_at.isoformat()
            },
            routing_key="event.new_post"
        )
        
        # Очищаем кэш
        await self.cache_interactions(db_post.group_id)
        
        return PostWithAuthor.from_orm(db_post)

    @handler_decorator
    async def update_post(self, post_id: int, post_data: PostUpdate) -> PostWithAuthor:
        """Обновление поста"""
        db_post = await self.is_author(post_id)

        update_data = post_data.dict(exclude_unset=True)
        for field in update_data:
            setattr(db_post, field, update_data[field])
        
        db_post.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(db_post)

        logger.info(f"Post {post_id} updated")

        # Очищаем кэш
        await self.cache_interactions(db_post.group_id)
        
        return PostWithAuthor.from_orm(db_post) 
    
    @handler_decorator
    async def get_post_by_id(self, post_id: int):
        return await self.interactions_with_post(post_id)

    @handler_decorator
    async def delete_post(self, post_id: int) -> PostWithAuthor:
        """Удаление поста"""

        db_post = await self.is_author(post_id)

        await self.db.execute(delete(Post).where(Post.id == db_post.id))
        await self.db.commit()

        logger.info(f"Post {post_id} deleted")

        # Очищаем кэш
        await self.cache_interactions(db_post.group_id)

        return PostWithAuthor.from_orm(db_post)
    
    ####PATTERNS####
    async def is_author(self, post_id):

        data_post = await self.interactions_with_post(post_id)

        if data_post.author.id != self.current_user.id:
            logger.warning("Только создатель может выполнить данную операцию")
            await self.handle_error(exception_cls=CreatorOnly)

        return data_post

    async def get_group_by_id(self, group_id: int):

        result = await self.db.execute(select(group_members.c.group_id).where(group_members.c.group_id == group_id))
        group = result.scalar()

        if not group:
            await self.handle_error(exception_cls=GroupNotFound, log_message=f"Group with id {group_id} not found")

        return group

    async def is_group_member(self, user_id: str, group_id: int):
        result = await self.db.execute(select(group_members.c.user_id).where((group_members.c.group_id == group_id) & (group_members.c.user_id == user_id)))
        
        return result.scalar() is not None

    async def interactions_with_post(self, post_id):

        logger.debug(f"Interaction with post: {post_id}")
        result = await self.db.execute(select(Post).filter(Post.id == post_id))
        db_post = result.scalars().first()
        if not db_post:
            logger.warning(f"Post {post_id} not found")
            await self.handle_error(exception_cls=PostNotFound)

        return db_post
        
    async def cache_interactions(self, group_id):
        await cache.delete("post_list")
        await cache.delete(f"group_posts:{group_id}")

    async def handle_error(self, exception_cls: type[Exception], cache_ttl: int = 10, log_message: str | None = None):
        cache_key = f"error:{self.current_user.id}:{exception_cls.__name__}"
        await cache.set(cache_key, {"type": exception_cls.__name__, "message": log_message}, ttl=cache_ttl)

        keys_list = await cache.get(f"error_keys:{self.current_user.id}") or []
        if cache_key not in keys_list:
            keys_list.append(cache_key)
            await cache.set(f"error_keys:{self.current_user.id}", keys_list, ttl=cache_ttl)

        if log_message:
            logger.error(log_message)

        raise exception_cls()
    ####PATTERNS####
