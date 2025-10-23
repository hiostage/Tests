import threading
from typing import TYPE_CHECKING

from app_utils.janitor import janitor
from rabbit_consumer.consumer import rabbit_consumer

if TYPE_CHECKING:

    from core.classes.app import CustomFastApi


def run_consumer(app: "CustomFastApi") -> None:
    """
    Запускает RabbitMQ consumer в отдельном демоническом потоке.

    :param app: Экземпляр приложения CustomFastApi, необходимый для работы consumer.
    """
    thread = threading.Thread(target=rabbit_consumer, args=(app,), daemon=True)
    thread.start()


def run_janitor(app: "CustomFastApi") -> None:
    """
    Запускает функцию сборщика мусора `janitor` в отдельном демоническом потоке.

    :param app: Экземпляр приложения CustomFastApi.
    """
    thread = threading.Thread(target=janitor, args=(app,), daemon=True)
    thread.start()


def print_debug_banner() -> None:
    """
    Выводит красное баннерное сообщение о включенном режиме отладки.
    """
    banner = """
    ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    ┃                                           ┃
    ┃  ⚠ DEBUG MODE ⚠   ВКЛЮЧЕН РЕЖИМ ОТЛАДКИ!  ┃
    ┃                                           ┃
    ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
    """
    print("\033[91m" + banner + "\033[0m")  # Красный цвет
