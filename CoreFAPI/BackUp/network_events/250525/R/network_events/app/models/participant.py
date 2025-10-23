from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint, String
from datetime import datetime
from app.db.database import Base

class Participant(Base):
    __tablename__ = "participants"
    __table_args__ = (UniqueConstraint("event_id", "user_id", name="unique_event_user"),)

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, nullable=False)  # из внешней системы
    registered_at = Column(DateTime, default=datetime.utcnow)
