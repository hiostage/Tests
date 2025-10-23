from typing import TYPE_CHECKING, Annotated, AsyncGenerator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi


async def get_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """
    Асинхронно создает и предоставляет сессию для работы с базой данных.

    :param request: Request.
    :return: AsyncGenerator[AsyncSession, None].
    """
    app: "CustomFastApi" = request.app
    db = app.get_db()
    session_maker = db.get_session_fabric()
    async with session_maker() as session:
        yield session


def get_session_maker(request: Request) -> async_sessionmaker[AsyncSession]:
    """
    Возвращает фабрику сессий.

    :param request: Request.
    :return: async_sessionmaker[AsyncSession].
    """
    app: "CustomFastApi" = request.app
    db = app.get_db()
    return db.get_session_fabric()


DbSessionDep = Annotated[AsyncSession, Depends(get_session)]
DbSessionMakerDep = Annotated[
    async_sessionmaker[AsyncSession], Depends(get_session_maker)
]
