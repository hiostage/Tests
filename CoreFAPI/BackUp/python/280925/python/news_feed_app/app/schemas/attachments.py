from typing import Optional

from fastapi import UploadFile  # noqa: TC002
from pydantic import BaseModel, ConfigDict, Field
from schemas.base import BaseSchema


class INAttachment(BaseModel):
    """
    In-схема вложения.
    """

    file: UploadFile
    caption: Optional[str]


class BaseOutAttachmentSchema(BaseModel):
    """
    Базовая out-схема вложения.
    """

    id: int
    attachment_path: str = Field(alias="url")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class OutAttachmentSchema(BaseOutAttachmentSchema):
    """
    Полная out-схема вложения.
    """

    caption: Optional[str]


class OutCreateAttachmentSchema(BaseSchema):
    """
    Out-схема вложения при создании.
    """

    media: BaseOutAttachmentSchema
