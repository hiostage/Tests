from typing import TYPE_CHECKING, Any, Callable, Coroutine

from app_utils.permission import check_route_permission
from dependencies.user import CurrentUserDep  # noqa: TC002
from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError

if TYPE_CHECKING:

    from schemas.users import Role, User


def is_valid_image(file: UploadFile) -> bool:
    """
    Проверяет, является ли файл корректным изображением.

    :param file: Загруженный файл (UploadFile).
    :return: True, если файл является корректным изображением, иначе False.
    """
    try:
        # Открываем изображение, если оно невалидное, Pillow выбросит ошибку
        img = Image.open(file.file)
        img.verify()  # Проверяем, является ли это действительно изображением

        # Сбрасываем указатель файла, так как .verify() его изменяет
        file.file.seek(0)
    except UnidentifiedImageError:
        return False
    return True


async def validate_image(file: UploadFile) -> UploadFile:
    """
    Валидатор для проверки, что файл является корректным изображением.

    :param file: Загруженный файл.
    :return: Файл, если он является корректным изображением.
    :raises HTTPException: Если файл не является изображением.
    """
    if not is_valid_image(file):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл не является корректным изображением.",
        )
    return file


def validate_user_permission(
    *required_roles: "Role",
) -> Callable[[CurrentUserDep], Coroutine[Any, Any, "User"]]:
    """
    Валидатор для проверки прав пользователя.

    :param required_roles: Список ролей, которые имеют доступ к эндпоинту.
    :return: Callable[[CurrentUserDep], Coroutine[Any, Any, User]]
    """

    async def wrap(user: CurrentUserDep) -> "User":
        """
        Принимает пользователя и проверяет его права с переданными правами.

        :param user: Текущий пользователь.
        :return: Пользователь, если у него есть права.
        :raises HTTPException: Если доступ запрещен.
        """
        if not check_route_permission(user, *required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Доступ запрещён."
            )
        return user

    return wrap
