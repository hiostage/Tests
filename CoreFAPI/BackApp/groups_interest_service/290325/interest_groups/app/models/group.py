from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON, Table
from sqlalchemy.orm import relationship
from app.models.base import Base
from datetime import datetime

# Ассоциативная таблица для связи групп и пользователей
group_members = Table(
    'group_members', 
    Base.metadata,
    Column('group_id', Integer, ForeignKey('groups.id'), primary_key=True, comment="ID группы"),
    Column('user_id', Integer, ForeignKey('users_cache.id'), primary_key=True, comment="ID пользователя"),
    Column('joined_at', DateTime, default=datetime.utcnow, comment="Дата вступления"),
    Column('role', String(50), default='member', comment="Роль в группе"),  # member, moderator, admin
    Column('is_banned', Boolean, default=False, comment="Забанен ли пользователь")
)

class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True, comment="Уникальный идентификатор")
    name = Column(String(100), unique=True, index=True, nullable=False, comment="Название группы")
    slug = Column(String(120), unique=True, index=True, comment="ЧПУ для URL")
    description = Column(Text, comment="Описание группы")
    category = Column(String(50), index=True, comment="Категория группы")  # technology, programming, hobbies и т.д.
    created_at = Column(DateTime, default=datetime.utcnow, index=True, comment="Дата создания")
    updated_at = Column(DateTime, onupdate=datetime.utcnow, comment="Дата обновления")
    creator_id = Column(Integer, ForeignKey("users_cache.id"), index=True, comment="ID создателя")
    is_public = Column(Boolean, default=True, comment="Публичная ли группа")
    banner_url = Column(String(255), comment="URL баннера группы")
    rules = Column(Text, comment="Правила группы")
    tags = Column(JSON, default=[], comment="Теги группы")
    
    # Связи с другими моделями
    members = relationship(
        "User", 
        secondary=group_members, 
        back_populates="groups",
        lazy="dynamic",  # Для пагинации участников
        collection_class=list,
        comment="Участники группы"
    )
    
    posts = relationship(
        "Post", 
        back_populates="group",
        lazy="dynamic",  # Для пагинации постов
        cascade="all, delete-orphan",
        comment="Посты в группе"
    )
    
    creator = relationship(
        "User", 
        back_populates="created_groups",
        lazy="selectin",  # Жадная загрузка создателя
        comment="Создатель группы"
    )

    def update_from_dict(self, data: dict):
        """Обновляет данные группы из словаря"""
        for key, value in data.items():
            if hasattr(self, key) and key not in ['id', 'created_at', 'creator_id']:
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()

    def get_member_count(self):
        """Возвращает количество участников"""
        return len(self.members) if isinstance(self.members, list) else self.members.count()

    def is_member(self, user_id: int) -> bool:
        """Проверяет, является ли пользователь участником группы"""
        if isinstance(self.members, list):
            return any(member.id == user_id for member in self.members)
        return self.members.filter_by(id=user_id).first() is not None