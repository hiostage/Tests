from celery import Celery
from app.celery_app import celery_app

@celery_app.task
def send_notification(*args, **kwargs):
    print(f"Received args: {args}, kwargs: {kwargs}")
    message = kwargs.get("message", None) or (args[0] if args else None)
    
    if not message:
        raise ValueError("No message provided")

    print(f"Sending notification: {message}")
    return f"Notification sent: {message}"
