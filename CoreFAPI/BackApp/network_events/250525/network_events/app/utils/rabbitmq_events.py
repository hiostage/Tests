from app.utils.rabbitmq import rabbitmq_publisher  # Импортируем твоего паблишера
import logging

logger = logging.getLogger("app")
async def send_participant_event(action: str, event_id: int, user_id: int) -> None:
    try:
        logger.info(f"Отправка события 'participant' в очередь 'event_participants' с action: {action}, event_id: {event_id}, user_id: {user_id}")
        await rabbitmq_publisher.publish(
            queue_name="event_participants",
            message={
                "action": action,
                "event_id": event_id,
                "user_id": user_id,
            }
        )
        logger.info(f"Событие 'participant' успешно отправлено в очередь 'event_participants'.")
    except Exception as e:
        logger.error(f"Ошибка при отправке события 'participant' в очередь 'event_participants': {e}")

async def send_event_event(event_id: int, action: str) -> None:
    try:
        logger.info(f"Отправка события 'event' в очередь 'event_updates' с action: {action}, event_id: {event_id}")
        await rabbitmq_publisher.publish(
            queue_name="event_updates",  # Одна очередь для обновлений событий
            message={
                "action": action,
                "event_id": event_id,
            }
        )
        logger.info(f"Событие 'event' успешно отправлено в очередь 'event_updates'.")
    except Exception as e:
        logger.error(f"Ошибка при отправке события 'event' в очередь 'event_updates': {e}")
