from logging import Logger
from typing import Annotated

from app_utils.permission import (
    admin_role,
    check_me_or_role,
)
from dependencies.loger import get_loger
from dependencies.services import AttachmentsServiceDep  # noqa: TC002
from fastapi import Depends, HTTPException, Query, status
from routers.media.access import MediaUser  # noqa: TC002
from routers.media.router import media_router
from schemas.base import BaseSchema
from schemas.exception_schema import ErrorSchema


@media_router.delete(
    "/news/media/image",
    response_model=BaseSchema,
    responses={
        403: {
            "description": "У пользователя нет прав на этот роут.",
            "model": ErrorSchema,
        },
        404: {"description": "Нет вложения с заданным id.", "model": ErrorSchema},
        400: {
            "description": "Пользователь не является хозяином изображения или отсутствуют повышенные права.",
            "model": ErrorSchema,
        },
    },
    name="Удаление изображения.",
    description="Удалит изображение (по его id) текущего пользователя (если он имеет право на это).",
)
async def media_delete_file(
    user: MediaUser,
    attachment_service: AttachmentsServiceDep,
    media_id: Annotated[int, Query(..., gt=0)],
    log: Annotated[Logger, Depends(get_loger("media_delete_file"))],
) -> BaseSchema:
    """
    Удалит изображение (по его id) текущего пользователя (если он имеет право на это).

    :param user: Текущий пользователь.
    :param attachment_service: Сервис, для работы с вложениями.
    :param media_id: ID удаляемой картинки.
    :param log: Логгер функции media_delete_file.
    :return: BaseSchema.
    """

    attachment = await attachment_service.repo.get_or_404(media_id)
    if not check_me_or_role(user, attachment, [admin_role]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Только хозяин или админ может удалить изображение.",
        )
    log.info(
        "Пользователь: id=%s. "
        "Начинаю удалять записи в БД и Minio. "
        "Attachment: id=%s. "
        "path: %s",
        user.id,
        attachment.id,
        attachment.attachment_path,
    )

    # Удаляем данные.
    attachment_service.fake_delete(attachment)
    await attachment_service.repo.commit()

    log.info("Пользователь: id=%s. Записи в БД успешно удалены.", user.id)
    return BaseSchema()
