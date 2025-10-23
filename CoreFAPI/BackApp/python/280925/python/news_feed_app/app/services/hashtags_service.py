from typing import List, Sequence

from database.models.hashtags import Hashtags
from repositories.hashtags import HashtagsRepository
from services.base_service import BaseService


class HashtagsService(BaseService[HashtagsRepository]):
    """
    Сервис для работы с вложениями (Hashtags).
    """

    async def get_or_create_by_hashtag_names(
        self, hashtag_names: Sequence[str]
    ) -> Sequence[Hashtags]:
        """
        Получает или создаёт хэштеги по их именам.

        :param hashtag_names: Список имен хэштегов для обработки
        :return: Список объектов Hashtags, соответствующих переданным именам

        Процесс:
        1. Проверяет существование хэштегов в базе данных.
        2. Если хэштеги существуют, добавляет их в результат.
        3. Создаёт новые хэштеги для имен, которые не найдены в базе.
        4. Добавляет новые хэштеги в сессию базы данных и в результат.
        """
        exists_hashtags = await self.repo.get_filter(
            self.repo.model.name.in_(hashtag_names)
        )
        response_list: List[Hashtags] = []
        if exists_hashtags:
            response_list.extend(exists_hashtags)
            exists_hashtag_names = [tag.name for tag in exists_hashtags]
            new_hashtags = [
                Hashtags(name=tag_name)
                for tag_name in hashtag_names
                if tag_name not in exists_hashtag_names
            ]
        else:
            new_hashtags = [Hashtags(name=tag_name) for tag_name in hashtag_names]
        if new_hashtags:
            self.repo.session.add_all(new_hashtags)
            response_list.extend(new_hashtags)
        return response_list
