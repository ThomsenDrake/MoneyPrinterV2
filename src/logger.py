"""
Logging configuration for MoneyPrinterV2.

This module sets up a comprehensive logging framework with:
- File logging with rotation
- Console logging with appropriate levels
- Structured logging format
- Separate loggers for different modules
"""

import logging
import logging.handlers
from pathlib import Path

from constants import (
    APP_LOG_BACKUP_COUNT,
    APP_LOG_MAX_BYTES,
    ERROR_LOG_BACKUP_COUNT,
    ERROR_LOG_MAX_BYTES,
)

# Create logs directory if it doesn't exist
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Log file paths
MAIN_LOG_FILE = LOGS_DIR / "moneyprinter.log"
ERROR_LOG_FILE = LOGS_DIR / "errors.log"

# Logging format
DETAILED_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
SIMPLE_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"


def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_to_console: bool = True,
) -> logging.Logger:
    """
    Set up a logger with file and console handlers.

    Args:
        name: Logger name (usually __name__ of the module)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to file
        log_to_console: Whether to log to console

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent duplicate handlers if logger already exists
    if logger.handlers:
        return logger

    # File handler with rotation
    if log_to_file:
        file_handler = logging.handlers.RotatingFileHandler(
            MAIN_LOG_FILE,
            maxBytes=APP_LOG_MAX_BYTES,
            backupCount=APP_LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(DETAILED_FORMAT))
        logger.addHandler(file_handler)

        # Error file handler (only errors and critical)
        error_handler = logging.handlers.RotatingFileHandler(
            ERROR_LOG_FILE,
            maxBytes=ERROR_LOG_MAX_BYTES,
            backupCount=ERROR_LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(DETAILED_FORMAT))
        logger.addHandler(error_handler)

    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)  # Only warnings+ to console
        console_handler.setFormatter(logging.Formatter(SIMPLE_FORMAT))
        logger.addHandler(console_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger with the standard configuration.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return setup_logger(name)


# Create a default application logger
app_logger = setup_logger("moneyprinter", level=logging.INFO)


# Convenience functions for the default logger
def debug(message: str, *args, **kwargs) -> None:
    """Log a debug message."""
    app_logger.debug(message, *args, **kwargs)


def info(message: str, *args, **kwargs) -> None:
    """Log an info message."""
    app_logger.info(message, *args, **kwargs)


def warning(message: str, *args, **kwargs) -> None:
    """Log a warning message."""
    app_logger.warning(message, *args, **kwargs)


def error(message: str, *args, exc_info: bool = False, **kwargs) -> None:
    """Log an error message."""
    app_logger.error(message, *args, exc_info=exc_info, **kwargs)


def critical(message: str, *args, exc_info: bool = False, **kwargs) -> None:
    """Log a critical message."""
    app_logger.critical(message, *args, exc_info=exc_info, **kwargs)
