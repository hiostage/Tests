from database.models import Posts
from repositories.base_repositories import BaseRepository
from sqlalchemy import select
from sqlalchemy.orm import selectinload


class PostsRepository(BaseRepository[Posts]):
    """
    Репозиторий для работы с сущностью Posts.
    """

    type_model = Posts

    async def get_post_with_repost(self, post_id: int) -> Posts | None:
        """
        Получает пост вместе с информацией о репосте (оригинальным постом).

        Выполняет запрос к базе данных, загружая связанную сущность `original_post`
        через JOIN для оптимального выполнения одного запроса.

        :param post_id: ID искомого поста
        :return: Объект поста с заполненным original_post или None, если пост не найден
        """
        stmt = (
            select(self.model)
            .where(Posts.id == post_id)
            .options(selectinload(Posts.original_post))
        )
        post_q = await self.session.execute(stmt)
        return post_q.scalars().one_or_none()
