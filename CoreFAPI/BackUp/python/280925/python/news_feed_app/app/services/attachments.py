from typing import TYPE_CHECKING, Sequence

from fastapi import HTTPException
from minio.error import MinioException
from repositories.attachments import AttachmentsRepository
from services.base_service import BaseService
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError

if TYPE_CHECKING:
    from logging import Logger

    from app_utils.minio_manager import MinioManager
    from database.models import Attachments
    from schemas.attachments import INAttachment
    from schemas.users import User


class AttachmentsService(BaseService[AttachmentsRepository]):
    """
    Сервис для работы с вложениями (Attachments).
    """

    async def get_by_ids_no_post(
        self, attachments_ids: Sequence[int], user: "User"
    ) -> Sequence["Attachments"]:
        """
        Возвращает вложения по списку ID, принадлежащие пользователю, но не привязанные к посту.

        :param attachments_ids: Список ID вложений
        :param user: Пользователь-владелец
        :return: Список вложений
        """
        return await self.repo.get_filter(
            and_(
                self.repo.model.user_id == user.id,
                self.repo.model.id.in_(attachments_ids),
                self.repo.model.post_id.is_(None),
            )
        )

    async def safe_saving_media_data(
        self,
        user: "User",
        in_attachment: "INAttachment",
        minio_manager: "MinioManager",
        log: "Logger",
    ) -> "Attachments":
        """
        Сохраняет медиаданные (файл) в MinIO и информацию о вложении в базу данных.

        Ожидаемое поведение:
        - Файл загружается в MinIO.
        - В базу данных сохраняется информация о вложении (путь к файлу и ID пользователя).
        - Если возникает ошибка в базе данных:
          - Откатывается транзакция.
          - Удаляется файл из MinIO (если он был загружен).
          - Вызывается исключение HTTPException с кодом 500.
        - Если возникает ошибка в MinIO:
          - Откатывается транзакция.
          - Вызывается исключение HTTPException с кодом 500.

        :param user: Пользователь, загружающий файл.
        :param in_attachment: Данные вложения.
        :param minio_manager: Менеджер для работы с MinIO.
        :param log: Логгер для записи ошибок.
        :return: Объект вложения (Attachments), если сохранение прошло успешно.
        :raises HTTPException: Если произошла ошибка при сохранении в базу данных или MinIO.
        """
        minio_manager.set_upload_file(in_attachment.file)
        attachment = self.repo.create(
            data=dict(
                attachment_path=minio_manager.get_file_url(),
                user_id=user.id,
                caption=in_attachment.caption,
            )
        )
        try:
            await minio_manager.save_file()
            await self.repo.session.flush()
        except SQLAlchemyError as e:
            # Если ошибка в базе данных, откатываем транзакцию и удаляем файл из MinIO
            await self.repo.session.rollback()
            await minio_manager.delete_file()
            log.error("Ошибка при сохранении в базу данных: %s", str(e))
            raise HTTPException(
                status_code=500, detail="Ошибка при сохранении в базу данных."
            )
        except MinioException as e:
            # Если ошибка в MinIO, откатываем транзакцию
            await self.repo.session.rollback()
            log.error("Ошибка при сохранении файла в MinIO: %s", str(e))
            raise HTTPException(
                status_code=500, detail="Ошибка при сохранении файла в MinIO."
            )
        else:
            await self.repo.session.commit()
        return attachment

    @staticmethod
    def fake_delete(attachment: "Attachments") -> None:
        """
        Помечает вложение, как удалённое

        :param attachment: Объект Attachments, который будет 'удален'
        """
        attachment.is_deleted = True
        attachment.post_id = None
