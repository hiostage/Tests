import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
import json
from pythonjsonlogger import jsonlogger

def setup_logger(name: str, log_file: str = None, level: str = "INFO"):
    """
    Настройка логгера с консольным и файловым выводом
    
    :param name: Имя логгера (например, 'rabbitmq')
    :param log_file: Путь к файлу логов (None - только консоль)
    :param level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Форматтеры
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    json_format = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Консольный вывод
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # Файловый вывод (если указан файл)
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(json_format)
        logger.addHandler(file_handler)
    
    return logger