import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(log_level=logging.INFO):
    """
    Sets up logging configuration for the application.

    :param log_level: Logging level (default is logging.INFO)
    """
    log_directory = "logs"
    os.makedirs(log_directory, exist_ok=True)
    log_file_path = os.path.join(log_directory, "app.log")

    if os.path.exists(log_file_path):
        open(log_file_path, "w").close()

    logger = logging.getLogger()
    logger.setLevel(log_level)

    if logger.hasHandlers():
        logger.handlers.clear()

    log_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    file_handler = RotatingFileHandler(
        log_file_path, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(log_level)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(log_level)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info("Logging is set up and log file cleared.")
