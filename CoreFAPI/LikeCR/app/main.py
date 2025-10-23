from fastapi import FastAPI
from app.tasks import send_notification  # Импорт таски Celery
from app.routes import router  # <-- Импортируем router, а не функцию!

app = FastAPI()

app.include_router(router, prefix="/api", tags=["likes"])

# Эндпоинт для теста Celery
@app.get("/send/")
def send_message(msg: str):
    task = send_notification.delay(msg)
    return {"task_id": task.id}
