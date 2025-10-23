from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, DateTime
from datetime import datetime

class CustomBase:
    """
    Базовый класс моделей с общими полями и методами.
    Добавляет стандартные поля ID и временные метки ко всем моделям.
    """
    
    id = Column(Integer, primary_key=True, index=True, comment="Уникальный идентификатор")
    created_at = Column(DateTime, default=datetime.utcnow, comment="Дата создания записи")
    updated_at = Column(DateTime, onupdate=datetime.utcnow, comment="Дата последнего обновления")

    def __repr__(self):
        """Строковое представление объекта для отладки"""
        return f"<{self.__class__.__name__}(id={self.id})>"

    def to_dict(self):
        """Преобразует модель в словарь (исключая приватные атрибуты)"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
            if not column.name.startswith('_')
        }

    def update_from_dict(self, data: dict, exclude: list = None):
        """
        Обновляет модель из словаря данных.
        :param data: Словарь с данными для обновления
        :param exclude: Список полей, которые не следует обновлять
        """
        exclude = exclude or []
        for key, value in data.items():
            if hasattr(self, key) and key not in exclude and not key.startswith('_'):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()

# Создаем базовый класс с нашей кастомной функциональностью
Base = declarative_base(cls=CustomBase)

# Добавляем метод для всех моделей
Base.metadata.info['description'] = "База данных приложения"