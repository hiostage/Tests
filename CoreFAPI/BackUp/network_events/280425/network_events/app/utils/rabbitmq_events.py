from app.utils.rabbitmq import rabbitmq_publisher  # Импортируем твоего паблишера

async def send_participant_event(action: str, event_id: int, user_id: int) -> None:
    await rabbitmq_publisher.publish(
        queue_name="event_participants",
        message={
            "action": action,
            "event_id": event_id,
            "user_id": user_id,
        }
    )
