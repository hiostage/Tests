from typing import TYPE_CHECKING

from pika import BlockingConnection, ConnectionParameters, PlainCredentials

if TYPE_CHECKING:
    from core.classes.settings import Settings


class RabbitMQClient:
    """
    Клиент для работы с RabbitMQ
    """

    def __init__(self, settings: "Settings"):
        """
        Инициализирует клиент с параметрами подключения из настроек.

        :param settings: Объект настроек приложения, содержащий конфигурацию RabbitMQ.
        """
        rab_set = settings.RABBITMQ_SETTINGS
        self.__connection_params = ConnectionParameters(
            host=rab_set.RABBITMQ_DEFAULT_HOST,
            port=int(rab_set.RABBITMQ_DEFAULT_PORT),
            credentials=PlainCredentials(
                username=rab_set.RABBITMQ_DEFAULT_USER,
                password=rab_set.RABBITMQ_DEFAULT_PASS,
            ),
        )
        self.__base_routing_key = rab_set.MQ_ROUTING_KEY
        self.__inner_routing_key = rab_set.INNER_MQ_ROUTING_KEY

    @property
    def base_routing_key(self) -> str:
        """
        Возвращает базовый ключ маршрутизации для RabbitMQ.

        :return: Ключ маршрутизации.
        """
        return self.__base_routing_key

    @property
    def inner_routing_key(self) -> str:
        """
        Возвращает внутренний ключ маршрутизации сообщений.

        :return: Внутренний ключ маршрутизации (str).
        """
        return self.__inner_routing_key

    def get_connection(self) -> BlockingConnection:
        """
        Создаёт и возвращает новое блокирующее подключение к RabbitMQ.

        :return: Объект блокирующего подключения к RabbitMQ.
        :raises AMQPConnectionError: Если не удалось установить соединение.
        """
        return BlockingConnection(parameters=self.__connection_params)
