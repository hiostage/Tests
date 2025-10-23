import uvicorn
from app_utils.exception_handlers import app_exception_handlers
from app_utils.lifespan import lifespan_func
from core.factory_function import get_app
from routers.app_routers import routers
from settings.app_settings import settings

if __name__ == "__main__":
    debug_settings = settings.model_copy(update={"DEBUG": True})
    app_debug = get_app(
        settings=debug_settings,
        lifespan=lifespan_func,
        routers=routers,
        exception_handlers=app_exception_handlers,
    )
    uvicorn.run(app_debug, host="127.0.0.1", port=8000)
