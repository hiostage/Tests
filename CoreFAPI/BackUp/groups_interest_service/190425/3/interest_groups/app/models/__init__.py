from app.models.base import Base
from app.models.user import User
from app.models.group import Group, group_members
from app.models.post import Post

# Автоматический импорт всех моделей (для Alembic)
# Это нужно для автоматического обнаружения моделей при создании миграций
import inspect
import sys
import os

def get_all_models():
    """Динамически собирает все модели из текущего модуля"""
    current_module = sys.modules[__name__]
    models = []
    
    for name, obj in inspect.getmembers(current_module):
        if inspect.isclass(obj) and issubclass(obj, Base) and obj != Base:
            models.append(obj)
    
    return models

# Экспортируем все модели для удобства импорта
__all__ = [
    "Base",
    "User", 
    "Group",
    "Post",
    "group_members",
    "get_all_models"  # Добавляем новую функцию в экспорт
]

# Инициализация моделей (при необходимости)
def init_models(engine):
    """Инициализация моделей (создание таблиц)"""
    Base.metadata.create_all(bind=engine)