from typing import Any

from database.models import Comments
from repositories.base_repositories import BaseRepository


class CommentsRepository(BaseRepository[Comments]):
    """
    Репозиторий для работы с моделью Comments.
    """

    type_model = Comments

    async def create_and_save(self, data: dict[str, Any]) -> Comments:
        """
         Создание и сохранения комментария в БД

        :param data: Атрибуты объекта комментарий
        :return: созданный комментарий
        """
        new_comment = self.create(data)
        await self.session.commit()
        return new_comment
