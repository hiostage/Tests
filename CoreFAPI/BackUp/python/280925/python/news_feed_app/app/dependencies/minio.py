from typing import TYPE_CHECKING, Annotated

from app_utils.minio_manager import MinioManager
from fastapi import Depends, Request
from minio import Minio

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi


def get_minio_manager(request: Request) -> MinioManager:
    """
    Возвращает MinioManager.

    :param request: Request.
    :return: MinioManager.
    """
    app: "CustomFastApi" = request.app
    return MinioManager(
        settings=app.get_settings(), minio_client=app.get_minio_client()
    )


def get_minio_client(request: Request) -> Minio:
    """
    Возвращает Minio client.

    :param request: Request.
    :return: Minio.
    """
    app: "CustomFastApi" = request.app
    return app.get_minio_client()


MinioClientDep = Annotated[Minio, Depends(get_minio_client)]
MinioManagerDep = Annotated[MinioManager, Depends(get_minio_manager)]
