from database.models.attachments import Attachments
from repositories.base_repositories import BaseRepository


class AttachmentsRepository(BaseRepository[Attachments]):
    """
    Репозиторий для работы с моделью "Вложения" (Attachments).
    """

    type_model = Attachments
