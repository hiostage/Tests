from .celery_worker import celery_app

@celery_app.task
def send_notification(message: str):
    print(f"Sending notification: {message}")
    return f"Notification sent: {message}"
