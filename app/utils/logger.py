import logging
import sys
from app.settings import settings

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    
    # Return immediately if handlers already exist to prevent duplicates
    if logger.handlers:
        return logger
        
    logger.setLevel(settings.LOG_LEVEL)

    # Console Handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(settings.LOG_LEVEL)

    # Formatting
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger
