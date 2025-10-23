# app/utils/logger.py
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

def setup_logging(log_dir="logs", log_file="app.log", max_bytes=1048576, backup_count=5):
    """
    Настройка логирования с выводом в консоль и файл с ротацией.
    """
    # Создаем директорию для логов, если её нет
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # Форматтер для логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Логгер для приложения
    logger = logging.getLogger("interest_groups")
    logger.setLevel(logging.INFO)
    
    # Обработчик для вывода в файл с ротацией
    file_handler = RotatingFileHandler(
        filename=f"{log_dir}/{log_file}",
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    file_handler.setFormatter(formatter)
    
    # Обработчик для вывода в консоль
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Добавляем обработчики к логгеру
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Инициализируем логгер при импорте
logger = setup_logging()