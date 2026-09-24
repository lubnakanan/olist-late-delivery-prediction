import logging
from pathlib import Path

from src.config import PROJECT_ROOT, load_config


def get_logger(name: str) -> logging.Logger:
    """Create (or reuse) a logger that writes to both console and a log file."""
    config = load_config()
    log_level = config["logging"]["level"]
    log_file = PROJECT_ROOT / config["logging"]["log_file"]

    # Make sure the logs/ folder exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers if the logger already has them
    if not logger.handlers:
        logger.setLevel(log_level)

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger