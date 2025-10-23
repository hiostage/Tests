from typing import Any, Protocol, Sequence

from schemas.users import Role, User

# TODO: Узнать о ролях. Временное решение.
admin_role = Role(name="admin")
news_maker_role = Role(name="news_maker")
anonymous_role = Role(name="anonymous")
auth_user = Role(name="auth_user")


def check_route_permission(user: User, *permissions: Role) -> bool:
    """
    Функция проверит пользователя. Если хоть одна роль совпадает, вернёт True, иначе False.

    :param user: Текущий пользователь.
    :param permissions: Последовательность ролей, которые имеют доступ.
    :return: True/False.
    """
    user_role_set = set(role.name.lower() for role in user.roles)
    permission_role_set = set(permission.name.lower() for permission in permissions)

    return bool(user_role_set & permission_role_set)


class CheckObject(Protocol):
    """
    Протокол объекта, который должен иметь user_id.
    """

    user_id: Any


def check_me_or_role(user: User, obj: CheckObject, roles: Sequence[Role]) -> bool:
    """
    Проверит, является ли пользователь хозяином объекта,
    если нет, проверит его роли на совпадение с переданными,
    в случае хоть одного положительного результата вернёт True, иначе False.

    :param user: Текущий пользователь.
    :param obj: Интересующий нас объект с user_id: UUID.
    :param roles: Последовательность ролей.
    :return: True/False.
    """
    if user.id == obj.user_id:
        return True
    user_role_set = set(user_role.name.lower() for user_role in user.roles)
    permission_role_set = set(role.name.lower() for role in roles)
    return bool(user_role_set & permission_role_set)
