from typing import Annotated, Optional

from app_utils.validators import validate_image
from database.models.attachments import MAX_CAPTION_LENGTH
from fastapi import Depends, File, Query, UploadFile
from schemas.attachments import INAttachment


def get_in_attachment(
    file: "AttachmentFileDep", caption: "AttachmentCaptionDep" = None
) -> INAttachment:
    """
    Создаёт объект INAttachment из загруженного файла и его описания.

    :param file: Объект с изображением.
    :param caption: Необязательное описание вложения.
    :return: Объект INAttachment с файлом и описанием.
    """
    if caption is not None:
        caption = caption.strip()
        caption = caption if caption else None
    return INAttachment(caption=caption, file=file)


AttachmentCaptionDep = Annotated[
    Optional[str],
    Query(
        ...,
        max_length=MAX_CAPTION_LENGTH,
        description="Описание вложения (необязательный параметр).",
    ),
]  # Необязательное описание вложения.


AttachmentFileDep = Annotated[
    UploadFile, File(..., media_type="image/*"), Depends(validate_image)
]  # Загружаемый файл изображения.


AttachmentDep = Annotated[
    INAttachment, Depends(get_in_attachment)
]  # Объект INAttachment, созданный из загруженного файла и его описания.
