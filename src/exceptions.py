"""
Custom exception hierarchy for MoneyPrinterV2.

This module defines a comprehensive exception hierarchy that provides:
1. Clear exception types for different error categories
2. Consistent error messaging
3. Error context preservation
4. Standard error handling patterns

Usage:
    from exceptions import ConfigurationError, APIError

    # Raise specific exceptions
    raise ConfigurationError("Missing API key", key="mistral_api_key")

    # Or use with context
    try:
        # ... some operation
    except requests.RequestException as e:
        raise APIError("Failed to connect to Mistral API", cause=e)
"""

import logging
from typing import Any, Optional


class MoneyPrinterError(Exception):
    """
    Base exception class for all MoneyPrinterV2 errors.

    All custom exceptions inherit from this base class, allowing
    for catch-all error handling when needed.

    Attributes:
        message: Human-readable error message
        cause: The original exception that caused this error (if any)
        context: Additional context information about the error
    """

    def __init__(
        self,
        message: str,
        cause: Optional[Exception] = None,
        **context: Any,
    ):
        """
        Initialize the exception.

        Args:
            message: Error message
            cause: The original exception (for exception chaining)
            **context: Additional context key-value pairs
        """
        self.message = message
        self.cause = cause
        self.context = context
        super().__init__(message)

    def __str__(self) -> str:
        """Return detailed error message with context."""
        parts = [self.message]

        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            parts.append(f"Context: {context_str}")

        if self.cause:
            parts.append(f"Caused by: {type(self.cause).__name__}: {str(self.cause)}")

        return " | ".join(parts)


# Configuration Errors
class ConfigurationError(MoneyPrinterError):
    """Raised when there's a configuration-related error."""

    pass


class MissingConfigError(ConfigurationError):
    """Raised when a required configuration value is missing."""

    pass


class InvalidConfigError(ConfigurationError):
    """Raised when a configuration value is invalid."""

    pass


# API Errors
class APIError(MoneyPrinterError):
    """Base class for API-related errors."""

    pass


class APIConnectionError(APIError):
    """Raised when unable to connect to an external API."""

    pass


class APIAuthenticationError(APIError):
    """Raised when API authentication fails (invalid API key, etc.)."""

    pass


class APIRateLimitError(APIError):
    """Raised when API rate limit is exceeded."""

    pass


class APIResponseError(APIError):
    """Raised when API returns an unexpected or malformed response."""

    pass


# File Operation Errors
class FileOperationError(MoneyPrinterError):
    """Base class for file operation errors."""

    pass


class FileNotFoundError(FileOperationError):
    """Raised when a required file is not found."""

    pass


class FilePermissionError(FileOperationError):
    """Raised when lacking permissions to access a file."""

    pass


class FileLockError(FileOperationError):
    """Raised when unable to acquire a file lock."""

    pass


class CacheError(FileOperationError):
    """Raised when cache operations fail."""

    pass


# Browser/Selenium Errors
class BrowserError(MoneyPrinterError):
    """Base class for browser automation errors."""

    pass


class BrowserInitializationError(BrowserError):
    """Raised when browser fails to initialize."""

    pass


class ElementNotFoundError(BrowserError):
    """Raised when a Selenium element is not found."""

    pass


class BrowserTimeoutError(BrowserError):
    """Raised when a browser operation times out."""

    pass


class BrowserOperationError(BrowserError):
    """Raised when a browser operation fails."""

    pass


# Alias for application-level timeout errors (distinct from BrowserTimeoutError)
class TimeoutError(MoneyPrinterError):
    """Raised when an operation times out (non-browser specific)."""

    pass


# Video Processing Errors
class VideoProcessingError(MoneyPrinterError):
    """Base class for video processing errors."""

    pass


class ImageGenerationError(VideoProcessingError):
    """Raised when image generation fails."""

    pass


class AudioGenerationError(VideoProcessingError):
    """Raised when audio/TTS generation fails."""

    pass


class VideoRenderError(VideoProcessingError):
    """Raised when video rendering fails."""

    pass


# Account Management Errors
class AccountError(MoneyPrinterError):
    """Base class for account management errors."""

    pass


class AccountNotFoundError(AccountError):
    """Raised when an account is not found."""

    pass


class DuplicateAccountError(AccountError):
    """Raised when attempting to create a duplicate account."""

    pass


# Validation Errors
class ValidationError(MoneyPrinterError):
    """Base class for validation errors."""

    pass


class InputValidationError(ValidationError):
    """Raised when user input is invalid."""

    pass


class PathValidationError(ValidationError):
    """Raised when a file path is invalid or potentially dangerous."""

    pass


# Subprocess Errors
class SubprocessError(MoneyPrinterError):
    """Base class for subprocess execution errors."""

    pass


class SubprocessTimeoutError(SubprocessError):
    """Raised when a subprocess times out."""

    pass


class SubprocessFailedError(SubprocessError):
    """Raised when a subprocess exits with a non-zero status."""

    pass


def log_exception(
    exception: Exception,
    logger: Optional[logging.Logger] = None,
    level: int = logging.ERROR,
    include_traceback: bool = True,
) -> None:
    """
    Log an exception with consistent formatting.

    This is a utility function for standardized exception logging.

    Args:
        exception: The exception to log
        logger: Logger instance (defaults to root logger)
        level: Logging level (default: ERROR)
        include_traceback: Whether to include full traceback

    Example:
        >>> try:
        ...     risky_operation()
        ... except Exception as e:
        ...     log_exception(e, logger, logging.WARNING)
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    # Build exception message
    if isinstance(exception, MoneyPrinterError):
        message = str(exception)  # Includes context and cause
    else:
        message = f"{type(exception).__name__}: {str(exception)}"

    # Log with or without traceback
    logger.log(level, message, exc_info=include_traceback)
