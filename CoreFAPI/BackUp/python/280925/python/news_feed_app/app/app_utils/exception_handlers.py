from typing import TYPE_CHECKING, Any

from fastapi import HTTPException, Request
from starlette.responses import JSONResponse

if TYPE_CHECKING:
    from core.classes.app import CustomFastApi


async def exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Хендлер исключений. Сработает, если в приложении возникнет ошибка Exception.

    :param request: Request.
    :param exc: Exception.
    :return: JSONResponse.
    """
    app: "CustomFastApi" = request.app
    loger = app.get_logger("exception_handler")
    loger.exception(exc)
    return JSONResponse(
        status_code=500,
        content={
            "result": False,
            "error_type": exc.__class__.__name__,
            "error_message": str(exc) if app.get_settings().DEBUG else "Error",
        },
    )


async def http_exception_handler(request: Request, exception: Any) -> JSONResponse:
    """
    Хендлер исключений. Сработает, если в приложении возникнет ошибка HTTPException.

    :param request: Request.
    :param exception: HTTPException. (mypy ругается на явную типизацию, поэтому Any)
    :return: JSONResponse.
    """
    exc: "HTTPException" = exception
    app: "CustomFastApi" = request.app
    loger = app.get_logger("http_exception_handler")
    loger.exception(exc)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "result": False,
            "error_type": exc.__class__.__name__,
            "error_message": exc.detail if app.get_settings().DEBUG else "Error",
        },
    )


app_exception_handlers = (
    (Exception, exception_handler),
    (HTTPException, http_exception_handler),
)
