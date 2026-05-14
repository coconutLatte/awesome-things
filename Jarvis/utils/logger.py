import sys
from pathlib import Path
from loguru import logger

_initialized = False


def setup_logger():
    global _initialized
    if _initialized:
        return

    from utils.config import get

    log_level = get("logging.level", "INFO")
    log_file = get("logging.file", "logs/jarvis.log")
    rotation = get("logging.rotation", "10 MB")

    log_path = Path(__file__).parent.parent / log_file
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.remove()
    logger.add(sys.stderr, level=log_level, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}")
    logger.add(str(log_path), level="DEBUG", rotation=rotation, retention="7 days", encoding="utf-8")

    _initialized = True
