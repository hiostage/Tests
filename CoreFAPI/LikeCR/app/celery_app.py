from celery import Celery

celery_app = Celery(
    "app",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    include=["app.celery_worker"]
)

celery_app.conf.update(
    task_serializer="pickle",
    accept_content=["json", "pickle"],
    result_serializer="pickle",
)


