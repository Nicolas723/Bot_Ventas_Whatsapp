import logging
import sys
from config import config

def setup_logger():
    logger = logging.getLogger("BekaBot")
    logger.setLevel(config.LOG_LEVEL)

    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
    )

    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Handler para archivo
    file_handler = logging.FileHandler(config.LOG_FILE, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

logger = setup_logger()
