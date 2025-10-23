from database.models.hashtags import Hashtags
from repositories.base_repositories import BaseRepository


class HashtagsRepository(BaseRepository[Hashtags]):
    """
    Репозиторий для работы с моделью "Вложения" (Hashtags).
    """

    type_model = Hashtags
