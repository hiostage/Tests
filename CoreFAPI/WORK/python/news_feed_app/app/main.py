from app_utils.exception_handlers import app_exception_handlers
from app_utils.lifespan import lifespan_func
from core.factory_function import get_app
from routers.app_routers import routers
from settings.app_settings import settings

app = get_app(
    settings=settings.model_copy(update={"DEBUG": True}),
    lifespan=lifespan_func,
    routers=routers,
    exception_handlers=app_exception_handlers,
)
