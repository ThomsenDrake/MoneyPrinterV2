"""
Error handling decorators and utilities for MoneyPrinterV2.

This module provides reusable error handling patterns through decorators:
1. @retry_on_failure - Automatic retry with exponential backoff
2. @handle_errors - Consistent error logging and handling
3. @safe_return - Return default value on error instead of raising
4. @log_errors - Log errors without changing behavior

Usage:
    from error_handlers import retry_on_failure, handle_errors, safe_return

    @retry_on_failure(max_attempts=3)
    def unstable_api_call():
        # ... API call that might fail

    @handle_errors(default_return=None, reraise=False)
    def process_file(path):
        # ... file processing

    @safe_return(default=[], log_level=logging.WARNING)
    def get_data():
        # ... returns empty list on error
"""

import functools
import logging
import time
from typing import Any, Callable, Optional, Tuple, Type, TypeVar

from exceptions import log_exception

# Type variable for generic functions
T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])


def retry_on_failure(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    logger: Optional[logging.Logger] = None,
) -> Callable[[F], F]:
    """
    Decorator to retry a function on failure with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts (default: 3)
        delay: Initial delay between retries in seconds (default: 1.0)
        backoff: Multiplier for delay after each attempt (default: 2.0)
        exceptions: Tuple of exception types to catch (default: (Exception,))
        logger: Logger for retry messages

    Returns:
        Decorated function that retries on failure

    Example:
        >>> @retry_on_failure(max_attempts=3, delay=2.0)
        ... def fetch_data():
        ...     return requests.get("https://api.example.com/data")

        >>> @retry_on_failure(exceptions=(requests.RequestException,))
        ... def api_call():
        ...     return client.chat.complete(...)
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            nonlocal logger
            if logger is None:
                logger = logging.getLogger(func.__module__)

            last_exception = None
            current_delay = delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {str(e)}",
                            exc_info=True,
                        )
                        raise

                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt}/{max_attempts}), "
                        f"retrying in {current_delay:.1f}s: {str(e)}"
                    )

                    time.sleep(current_delay)
                    current_delay *= backoff

            # This shouldn't be reached, but for type safety
            if last_exception:
                raise last_exception

        return wrapper  # type: ignore

    return decorator


def handle_errors(
    default_return: Any = None,
    reraise: bool = True,
    log_level: int = logging.ERROR,
    logger: Optional[logging.Logger] = None,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
) -> Callable[[F], F]:
    """
    Decorator for consistent error handling with logging.

    Catches specified exceptions, logs them, and either re-raises or returns default.

    Args:
        default_return: Value to return on error if not re-raising
        reraise: Whether to re-raise the exception after logging
        log_level: Logging level for errors
        logger: Logger instance
        exceptions: Tuple of exception types to catch

    Returns:
        Decorated function with error handling

    Example:
        >>> @handle_errors(default_return=False, reraise=False)
        ... def upload_video():
        ...     # ... upload logic
        ...     return True

        >>> @handle_errors(reraise=True, log_level=logging.WARNING)
        ... def validate_config():
        ...     # ... validation logic
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            nonlocal logger
            if logger is None:
                logger = logging.getLogger(func.__module__)

            try:
                return func(*args, **kwargs)
            except exceptions as e:
                # Log the exception
                log_exception(e, logger, log_level, include_traceback=True)

                # Either re-raise or return default
                if reraise:
                    raise
                else:
                    logger.info(f"{func.__name__} returning default value: {default_return}")
                    return default_return

        return wrapper  # type: ignore

    return decorator


def safe_return(
    default: Any = None,
    log_level: int = logging.WARNING,
    logger: Optional[logging.Logger] = None,
) -> Callable[[F], F]:
    """
    Decorator to return a default value on any exception.

    Similar to @handle_errors but always returns default without re-raising.
    Useful for non-critical operations where you want graceful degradation.

    Args:
        default: Value to return on error
        log_level: Logging level for errors
        logger: Logger instance

    Returns:
        Decorated function that never raises

    Example:
        >>> @safe_return(default=[])
        ... def get_cached_items():
        ...     # ... might fail but we want empty list
        ...     return items

        >>> @safe_return(default=None, log_level=logging.DEBUG)
        ... def get_optional_config(key):
        ...     return config[key]
    """
    return handle_errors(default_return=default, reraise=False, log_level=log_level, logger=logger)


def log_errors(
    log_level: int = logging.ERROR,
    logger: Optional[logging.Logger] = None,
    include_traceback: bool = True,
) -> Callable[[F], F]:
    """
    Decorator to log errors without changing function behavior.

    Logs exceptions but always re-raises them. Useful for adding logging
    to existing functions without changing their error handling.

    Args:
        log_level: Logging level for errors
        logger: Logger instance
        include_traceback: Whether to include full traceback

    Returns:
        Decorated function with error logging

    Example:
        >>> @log_errors(log_level=logging.WARNING)
        ... def risky_operation():
        ...     # ... might raise, but we want to log it
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            nonlocal logger
            if logger is None:
                logger = logging.getLogger(func.__module__)

            try:
                return func(*args, **kwargs)
            except Exception as e:
                log_exception(e, logger, log_level, include_traceback)
                raise

        return wrapper  # type: ignore

    return decorator


def validate_not_none(*arg_names: str) -> Callable[[F], F]:
    """
    Decorator to validate that specified arguments are not None.

    Raises ValueError if any specified argument is None.

    Args:
        *arg_names: Names of arguments to validate

    Returns:
        Decorated function with None validation

    Example:
        >>> @validate_not_none('api_key', 'endpoint')
        ... def call_api(api_key, endpoint, timeout=30):
        ...     # ... api_key and endpoint must not be None
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get function signature
            import inspect

            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Check specified arguments
            for arg_name in arg_names:
                if arg_name in bound_args.arguments:
                    value = bound_args.arguments[arg_name]
                    if value is None:
                        raise ValueError(
                            f"Argument '{arg_name}' cannot be None in {func.__name__}()"
                        )

            return func(*args, **kwargs)

        return wrapper  # type: ignore

    return decorator


def fallback_on_error(
    fallback_func: Callable[..., Any],
    log_message: Optional[str] = None,
    logger: Optional[logging.Logger] = None,
) -> Callable[[F], F]:
    """
    Decorator to call a fallback function on error.

    If the decorated function raises an exception, calls fallback_func instead.

    Args:
        fallback_func: Function to call on error
        log_message: Optional message to log
        logger: Logger instance

    Returns:
        Decorated function with fallback

    Example:
        >>> def use_cache(*args, **kwargs):
        ...     return cached_data

        >>> @fallback_on_error(use_cache, "API unavailable, using cache")
        ... def fetch_from_api():
        ...     return api_client.get_data()
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            nonlocal logger
            if logger is None:
                logger = logging.getLogger(func.__module__)

            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_message:
                    logger.warning(f"{log_message}: {str(e)}")
                else:
                    logger.warning(f"{func.__name__} failed, using fallback: {str(e)}")

                # Call fallback with same arguments
                return fallback_func(*args, **kwargs)

        return wrapper  # type: ignore

    return decorator


class ErrorContext:
    """
    Context manager for consistent error handling in with blocks.

    Usage:
        >>> with ErrorContext("Processing video", reraise=True):
        ...     # ... operations that might fail
        ...     process_video()

        >>> with ErrorContext("Fetching data", default_return=[], reraise=False) as ctx:
        ...     data = fetch_data()
        ...     ctx.set_result(data)
    """

    def __init__(
        self,
        operation_name: str,
        reraise: bool = True,
        default_return: Any = None,
        logger: Optional[logging.Logger] = None,
        log_level: int = logging.ERROR,
    ):
        """
        Initialize error context.

        Args:
            operation_name: Name of the operation for logging
            reraise: Whether to re-raise exceptions
            default_return: Value to return on error if not re-raising
            logger: Logger instance
            log_level: Logging level for errors
        """
        self.operation_name = operation_name
        self.reraise = reraise
        self.default_return = default_return
        self.logger = logger or logging.getLogger(__name__)
        self.log_level = log_level
        self.result: Any = None
        self.exception: Optional[Exception] = None

    def set_result(self, result: Any) -> None:
        """Set the result value."""
        self.result = result

    def __enter__(self) -> "ErrorContext":
        """Enter the context."""
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[Exception]],
        exc_val: Optional[Exception],
        exc_tb: Any,
    ) -> bool:
        """
        Exit the context and handle any exceptions.

        Returns:
            True if exception should be suppressed, False otherwise
        """
        if exc_val is not None:
            self.exception = exc_val

            # Log the exception
            log_exception(exc_val, self.logger, self.log_level, include_traceback=True)

            if self.reraise:
                return False  # Re-raise the exception
            else:
                self.logger.info(
                    f"{self.operation_name} failed, using default: {self.default_return}"
                )
                self.result = self.default_return
                return True  # Suppress the exception

        return False
