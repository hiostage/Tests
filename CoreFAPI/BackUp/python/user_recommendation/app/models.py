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

class UserSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    uuid: str
    firstName: str
    lastName: str
    userName: str
    email: str
    phone: Optional[str] = None
    roles: Optional[list[str]] = None
    location: str | None = None
    skills: list[str] = []
    purpose_cooperation: str | None = None


class PurposeCooperationSchema(str, enum.Enum):
    JOB_SEARCH = "job_search"
    PARTNERSSHIP = "partnership"
    EXCHANGE_EXPERIENCE = "exchange_experience"


class PrioritySchema(str, enum.Enum):
    LOCATION = "location"
