import asyncio
import os
import uuid
from typing import TYPE_CHECKING, Any, Coroutine, Dict, Iterator, Optional, Sequence

from minio.deleteobjects import DeleteError, DeleteObject

if TYPE_CHECKING:
    from core.classes.settings import Settings
    from fastapi import UploadFile
    from minio import Minio
    from minio.helpers import ObjectWriteResult


def get_image_name(file: "UploadFile") -> str:
    """
    Функция возвращает уникальное имя файла.

    :param file: Файл.

    :return: Уникальное имя файла.
    """
    filename = file.filename if file.filename else "example.jpg"
    _file_extension = os.path.splitext(filename)[1]
    file_extension = _file_extension if _file_extension else ".jpg"
    return str(uuid.uuid4()) + file_extension


def get_file_url(file_name: str, settings: "Settings") -> str:
    """
    Функция возвращает url файла относительно MinIO

    :param file_name: Имя файла.
    :param settings: Настройки приложения.

    :return: Url файла относительно MinIO.
    """
    return f"/{settings.MINIO_SETTINGS.MINIO_BUCKET}/{file_name}"


class MinioManager:
    """
    Класс-помощник для работы с MinIO.
    """

    __unique_filename: Optional[str] = None
    __file: Optional["UploadFile"] = None
    __file_url: Optional[str] = None

    def __init__(self, settings: "Settings", minio_client: "Minio") -> None:
        """
        Инициализация.

        :param settings: Настройки приложения.
        :param minio_client: MinIO клиент.

        :return: None.
        """
        self.__settings = settings
        self.__minio_client = minio_client

    def set_upload_file(self, file: "UploadFile") -> None:
        """
        Функция принимает файл.

        :param file: Объект сохраняемого файла.

        :return: None.
        """
        self.__file = file
        self.__unique_filename = get_image_name(file)
        self.__file_url = get_file_url(self.__unique_filename, self.__settings)

    def get_unique_filename(self) -> str:
        """
        Функция вернёт уникальное имя присвоенное файлу.

        :return: Уникальное имя присвоенное файлу.
        """
        if self.__unique_filename is None:
            raise ValueError(
                "Имя не существует. Воспользуйтесь методами 'set_upload_file' или 'set_file_url'."
            )
        return self.__unique_filename

    def get_file_url(self) -> str:
        """
        Функция возвращает url файла относительно MinIO.

        :return: Url файла относительно MinIO.
        """
        if self.__file_url is None:
            raise ValueError(
                "URL не существует. Воспользуйтесь методами 'set_upload_file' или 'set_file_url'."
            )
        return self.__file_url

    def set_file_url(self, file_url: str) -> None:
        """
        Функция принимает url файла относительно MinIO.

        :param file_url: Url файла относительно MinIO.

        :return: None.
        """
        self.__file_url = file_url
        self.__unique_filename = self.__file_url.split("/")[-1]
        self.__file = None

    def save_file(self) -> Coroutine[Any, Any, "ObjectWriteResult"]:
        """
        Функция вернёт корутину для сохранения файла.

        :return: Coroutine[Any, Any, ObjectWriteResult].
        """
        if self.__file is None:
            raise ValueError(
                "Объект сохраняемого файла не задан. Воспользуйтесь методом 'set_upload_file'"
            )
        param: Dict[str, Any] = dict(
            bucket_name=self.__settings.MINIO_SETTINGS.MINIO_BUCKET,
            object_name=self.__unique_filename,
            data=self.__file.file,
            length=self.__file.size,
            content_type=self.__file.content_type,
        )
        return asyncio.to_thread(self.__minio_client.put_object, **param)

    def sync_save_file(self) -> "ObjectWriteResult":
        """
        Сохраняет файл в хранилище MinIO синхронно.

        Проверяет, что файл был установлен через метод `set_upload_file`.
        Формирует параметры для загрузки и вызывает метод `put_object` клиента MinIO.

        :raises ValueError: если объект файла не установлен.
        :return: Объект результата записи `ObjectWriteResult` от MinIO.
        """
        if self.__file is None:
            raise ValueError(
                "Объект сохраняемого файла не задан. Воспользуйтесь методом 'set_upload_file'"
            )
        param: Dict[str, Any] = dict(
            bucket_name=self.__settings.MINIO_SETTINGS.MINIO_BUCKET,
            object_name=self.__unique_filename,
            data=self.__file.file,
            length=self.__file.size,
            content_type=self.__file.content_type,
        )
        return self.__minio_client.put_object(**param)

    def delete_file(self) -> Coroutine[Any, Any, None]:
        """
        Функция вернёт корутину для удаления файла.

        :return: Coroutine[Any, Any, None].
        """
        if self.__file_url is None:
            raise ValueError(
                "Url удаляемого файла не задан. Воспользуйтесь методом 'set_file_url'"
            )
        param: Dict[str, Any] = dict(
            bucket_name=self.__settings.MINIO_SETTINGS.MINIO_BUCKET,
            object_name=self.__unique_filename,
        )
        return asyncio.to_thread(self.__minio_client.remove_object, **param)

    def sync_delete_file(self) -> Any:
        """
        Удаляет файл из хранилища MinIO синхронно.

        Проверяет, что URL файла для удаления был установлен через метод `set_file_url`.
        Формирует параметры для удаления и вызывает метод `remove_object` клиента MinIO.

        :raises ValueError: если URL удаляемого файла не установлен.
        :return: Any
        """
        if self.__file_url is None:
            raise ValueError(
                "Url удаляемого файла не задан. Воспользуйтесь методом 'set_file_url'"
            )
        param: Dict[str, Any] = dict(
            bucket_name=self.__settings.MINIO_SETTINGS.MINIO_BUCKET,
            object_name=self.__unique_filename,
        )
        return self.__minio_client.remove_object(**param)

    def bulk_delete_files(
        self, files_url: Sequence[str]
    ) -> Coroutine[Any, Any, Iterator[DeleteError]]:
        """
        Удаляет файлы из хранилища MinIO в пакетном режиме.

        :param files_url: Список URL файлов для удаления.
        :return: Вернёт корутину для удаления файлов.

        Примечание:
        - Файлы удаляются на основе их имени, извлеченного из URL.
        - Операция выполняется в отдельном потоке через asyncio.to_thread.
        """
        param: Dict[str, Any] = dict(
            bucket_name=self.__settings.MINIO_SETTINGS.MINIO_BUCKET,
            delete_object_list=[DeleteObject(f.split("/")[-1]) for f in files_url],
        )
        return asyncio.to_thread(self.__minio_client.remove_objects, **param)

    def sync_bulk_delete_files(self, files_url: Sequence[str]) -> Iterator[DeleteError]:
        """
        Удаляет несколько файлов из хранилища MinIO синхронно.

        Формирует список объектов для удаления на основе переданных URL файлов.
        Вызывает метод `remove_objects` клиента MinIO для пакетного удаления.

        :param files_url: Последовательность URL файлов для удаления.
        :return: Итератор ошибок удаления `DeleteError`, если они возникнут.
        """
        param: Dict[str, Any] = dict(
            bucket_name=self.__settings.MINIO_SETTINGS.MINIO_BUCKET,
            delete_object_list=[DeleteObject(f.split("/")[-1]) for f in files_url],
        )
        return self.__minio_client.remove_objects(**param)
