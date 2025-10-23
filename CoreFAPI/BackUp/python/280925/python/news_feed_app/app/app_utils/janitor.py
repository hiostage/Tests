import time
from datetime import datetime
from typing import TYPE_CHECKING

from app_utils.minio_manager import MinioManager
from database.models import Attachments
from minio.error import MinioException
from sqlalchemy import and_, delete, or_, select
from sqlalchemy.exc import SQLAlchemyError

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi


def janitor(app: "CustomFastApi") -> None:
    """
    Фоновая задача - сборщик мусора для удаления устаревших и помеченных на удаление вложений.

    Периодически (с интервалом из настроек) выполняет:
    - Поиск вложений, помеченных как удалённые или старых и не связанных с постом.
    - Удаление файлов из MinIO.
    - Удаление соответствующих записей из базы данных.
    - Логирование процесса и ошибок.

    :param app: Экземпляр приложения CustomFastApi.
    """
    janitor_settings = app.get_settings().JANITOR_SETTINGS
    repeat_time = janitor_settings.REPEAT_TIME.total_seconds()
    session_maker = app.get_sync_db().get_sync_session_fabric()
    minio_client = app.get_minio_client()
    settings = app.get_settings()
    m_manager = MinioManager(settings=settings, minio_client=minio_client)
    log = app.get_logger("janitor")
    log.info("Запускается сборщик мусора. С интервалом: %s секунд", repeat_time)
    while True:
        try:
            with session_maker() as session:
                attachments = (
                    session.execute(
                        select(Attachments)
                        .filter(
                            or_(
                                Attachments.is_deleted.is_(True),
                                and_(
                                    Attachments.created_at
                                    < datetime.now()
                                    - janitor_settings.CONSIDER_OLD_FILE,
                                    Attachments.post_id.is_(None),
                                ),
                            )
                        )
                        .limit(janitor_settings.NUMBER_OF_FILES_AT_TIME)
                        .order_by(Attachments.id)
                    )
                    .scalars()
                    .all()
                )
                if attachments:
                    att_path = [att.attachment_path for att in attachments]
                    att_ids = [att.id for att in attachments]
                    log.info("Обнаружены файлы для удаления с path: %s.", att_path)
                    errors = m_manager.sync_bulk_delete_files(att_path)
                    for error in errors:
                        log.info(
                            "Ошибка при удалении %s: %s", error.name, error.message
                        )
                    session.execute(
                        delete(Attachments).where(Attachments.id.in_(att_ids))
                    )
                    session.commit()
                    log.info("Записи удалены и с БД и с Minio.")
        except SQLAlchemyError:
            log.warning(
                "Сборщик мусора неожиданно столкнулся с ошибкой при подключении к БД."
            )
        except MinioException:
            log.warning(
                "Сборщик мусора неожиданно столкнулся с ошибкой при подключении к Minio."
            )
        time.sleep(repeat_time)
