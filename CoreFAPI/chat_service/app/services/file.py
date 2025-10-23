from sqlalchemy.ext.asyncio import AsyncSession
from app.models.file import FileAttachment
from app.schemas.file import FileAttachmentBase

async def save_file(db: AsyncSession, file_data: FileAttachmentBase) -> FileAttachment:
    """Сохранить информацию о файле в базе данных."""
    new_file = FileAttachment(**file_data.model_dump())
    db.add(new_file)
    await db.commit()
    await db.refresh(new_file)
    return new_file
