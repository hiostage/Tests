from logging import Logger
from typing import Annotated

from dependencies.attachment import AttachmentDep  # noqa: TC002
from dependencies.loger import get_loger
from dependencies.minio import MinioManagerDep  # noqa: TC002
from dependencies.services import AttachmentsServiceDep  # noqa: TC002
from fastapi import Depends
from routers.media.access import MediaUser  # noqa: TC002
from routers.media.router import media_router
from schemas.attachments import (
    BaseOutAttachmentSchema,
    OutCreateAttachmentSchema,
)
from schemas.exception_schema import ErrorSchema


@media_router.post(
    "/news/media/image",
    response_model=OutCreateAttachmentSchema,
    responses={
        403: {
            "description": "У пользователя нет прав на этот роут.",
            "model": ErrorSchema,
        },
        400: {
            "description": "Файл не является корректным изображением.",
            "model": ErrorSchema,
        },
    },
    name="Загрузка изображения.",
    description="Загрузит и сохранит изображение текущего пользователя (если он имеет право на это).",
)
async def media_create_upload_file(
    user: MediaUser,
    minio_manager: MinioManagerDep,
    attachment_service: AttachmentsServiceDep,
    log: Annotated[Logger, Depends(get_loger("media_create_upload_file"))],
    in_attachment: AttachmentDep,
) -> OutCreateAttachmentSchema:
    """
    Загрузит и сохранит изображение текущего пользователя (если он имеет право на это).

    :param user: Текущий пользователь.
    :param minio_manager: MinIO менеджер.
    :param attachment_service: Сервис, для работы с вложениями.
    :param log: Логгер функции media_create_upload_file.
    :param in_attachment: Данные вложения.
    :return: OutAttachmentSchema.
    """
    log.info("Пользователь: id=%s. Начинаю делать записи в БД и Minio.", user.id)

    attachment = await attachment_service.safe_saving_media_data(
        user, in_attachment, minio_manager, log
    )

    log.info(
        "Пользователь: id=%s. Запись в БД успешно добавлена с id=%s.",
        user.id,
        attachment.id,
    )
    log.info(
        "Пользователь: id=%s. Успешная запись в Minio, получен path=%s.",
        user.id,
        minio_manager.get_file_url(),
    )

    return OutCreateAttachmentSchema(
        media=BaseOutAttachmentSchema.model_validate(attachment)
    )
