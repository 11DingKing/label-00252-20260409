"""Logging configuration using loguru."""
import sys
from loguru import logger
from app.core.config import settings

# Remove default handler
logger.remove()

# Add console handler with custom format
log_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)

logger.add(
    sys.stdout,
    format=log_format,
    level="DEBUG" if settings.DEBUG else "INFO",
    colorize=True
)

# Add file handler for production
logger.add(
    "logs/app.log",
    rotation="10 MB",
    retention="7 days",
    compression="zip",
    format=log_format,
    level="INFO"
)

# Add error file handler
logger.add(
    "logs/error.log",
    rotation="10 MB",
    retention="30 days",
    compression="zip",
    format=log_format,
    level="ERROR"
)


def get_logger(name: str):
    """Get a logger instance with the given name."""
    return logger.bind(name=name)
