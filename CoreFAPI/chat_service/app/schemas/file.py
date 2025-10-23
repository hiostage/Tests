from pydantic import BaseModel
from datetime import datetime

class FileAttachmentBase(BaseModel):
    message_id: int
    file_path: str
    filename: str

class FileAttachmentResponse(FileAttachmentBase):
    id: int
    uploaded_at: datetime

    class Config:
        from_attributes = True
