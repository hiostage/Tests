from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.db.databse import Base
from sqlalchemy.dialects.postgresql import JSONB
from pydantic import BaseModel, ConfigDict
import enum
from typing import Optional, Dict


class SkillLevel(str, enum.Enum):
    FUNDAMENTAL = "fundamental"
    MIDDLE = "middle"
    ADVANCED = "advanced"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    profile_photo: Mapped[str] = mapped_column(String, nullable=True)
    location: Mapped[str] = mapped_column(String, nullable=True)
    bio: Mapped[str] = mapped_column(String, nullable=True)
    skills: Mapped[dict[str, SkillLevel]] = mapped_column(JSONB, nullable=True)
    work_experience: Mapped[dict[str, str]] = mapped_column(JSONB, nullable=True)
    education: Mapped[str] = mapped_column(String, nullable=True)
    git_profile: Mapped[str] = mapped_column(String, nullable=True)
    desired_salary: Mapped[int] = mapped_column(Integer, nullable=True)
    profile_privacy: Mapped[str] = mapped_column(String, default="public")


class UserSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: str
    profile_photo: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None
    skills: Optional[Dict[str, str]] = None
    education: Optional[str] = None
    work_experience: Optional[Dict[str, str]] = None
    desired_salary: Optional[int] = None
    git_profile: Optional[str] = None
    profile_privacy: Optional[str] = None


class PurposeCooperationSchema(str, enum.Enum):
    JOB_SEARCH = "job_search"
    PARTNERSSHIP = "partnership"
    EXCHANGE_EXPERIENCE = "exchange_experience"


class PrioritySchema(str, enum.Enum):
    LOCATION = "location"
