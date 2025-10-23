from typing import Sequence
from uuid import UUID  # noqa: TC003

from pydantic import BaseModel


# TODO: Дописать, когда станет понятнее с пользователями.
class Role(BaseModel):
    """
    Роль пользователя.

    **name** Название.
    """

    name: str

    def __eq__(self, other: object) -> bool:
        """
        Функция сравнения.

        :param other: Другой объект Role.
        :return: True если имена совпадают, иначе False.
        """
        if not isinstance(other, Role):
            raise ValueError("Сравнивать Role нужно с Role.")
        return self.name.lower() == other.name.lower()


class User(BaseModel):
    """
    Схема пользователя.

    **id** ID пользователя.
    **roles** Последовательность ролей.
    """

    id: UUID | None
    roles: Sequence[Role]
