from typing import TYPE_CHECKING, Type, TypeVar

from database.models.base import Base
from sqlalchemy import select

if TYPE_CHECKING:
    from minio import Minio
    from sqlalchemy.ext.asyncio import AsyncSession
T = TypeVar("T", bound=Base)


async def has_records_in_bd(model: Type[T], session: "AsyncSession") -> bool:
    """
    Проверяет, есть ли записи в таблице.

    :param model: Модель таблицы (например, Attachments).
    :param session: Асинхронная сессия SQLAlchemy.

    :return: True, если есть записи, иначе False.
    """
    result = await session.execute(select(model))
    return bool(result.scalars().first())


def has_records_in_minio(minio_client: "Minio", bucket_name: str) -> bool:
    """
    Проверяет, есть ли записи (объекты) в MinIO.

    :param minio_client: Клиент MinIO.
    :param bucket_name: Имя бакета.

    :return: True, если есть записи, иначе False.
    """
    objects = minio_client.list_objects(bucket_name, recursive=True)
    for _ in objects:
        return True
    return False
