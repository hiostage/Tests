from sqlalchemy import Column, Integer, ForeignKey, String, DateTime
from datetime import datetime
from app.models.base import Base

class FileAttachment(Base):  
    __tablename__ = "file_attachments"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String, nullable=False)  # Путь к файлу
    filename = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
