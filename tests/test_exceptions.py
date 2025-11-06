"""Tests for custom exception hierarchy."""

import pytest

from src.exceptions import (
    APIAuthenticationError,
    APIConnectionError,
    APIError,
    APIRateLimitError,
    APIResponseError,
    BrowserError,
    BrowserInitializationError,
    ConfigurationError,
    ElementNotFoundError,
    FileNotFoundError,
    FileOperationError,
    InvalidConfigError,
    MissingConfigError,
    MoneyPrinterError,
    ValidationError,
    VideoProcessingError,
    log_exception,
)


class TestMoneyPrinterError:
    """Test the base exception class."""

    def test_basic_exception(self):
        """Test basic exception creation."""
        exc = MoneyPrinterError("Something went wrong")
        assert str(exc) == "Something went wrong"
        assert exc.message == "Something went wrong"
        assert exc.cause is None
        assert exc.context == {}

    def test_exception_with_cause(self):
        """Test exception with cause."""
        original = ValueError("Original error")
        exc = MoneyPrinterError("Wrapper error", cause=original)

        assert "Wrapper error" in str(exc)
        assert "ValueError" in str(exc)
        assert "Original error" in str(exc)
        assert exc.cause == original

    def test_exception_with_context(self):
        """Test exception with context."""
        exc = MoneyPrinterError("Config error", key="api_key", value="missing")

        assert "Config error" in str(exc)
        assert "key=api_key" in str(exc)
        assert "value=missing" in str(exc)
        assert exc.context == {"key": "api_key", "value": "missing"}

    def test_exception_with_cause_and_context(self):
        """Test exception with both cause and context."""
        original = FileNotFoundError("config.json not found")
        exc = MoneyPrinterError("Failed to load config", cause=original, path="/path/to/config")

        exc_str = str(exc)
        assert "Failed to load config" in exc_str
        assert "FileNotFoundError" in exc_str
        assert "path=/path/to/config" in exc_str


class TestExceptionHierarchy:
    """Test exception inheritance hierarchy."""

    def test_configuration_errors(self):
        """Test configuration error hierarchy."""
        exc = MissingConfigError("API key missing")
        assert isinstance(exc, ConfigurationError)
        assert isinstance(exc, MoneyPrinterError)

        exc = InvalidConfigError("Invalid timeout value")
        assert isinstance(exc, ConfigurationError)
        assert isinstance(exc, MoneyPrinterError)

    def test_api_errors(self):
        """Test API error hierarchy."""
        for exc_class in [
            APIConnectionError,
            APIAuthenticationError,
            APIRateLimitError,
            APIResponseError,
        ]:
            exc = exc_class("Test error")
            assert isinstance(exc, APIError)
            assert isinstance(exc, MoneyPrinterError)

    def test_file_errors(self):
        """Test file operation error hierarchy."""
        exc = FileNotFoundError("File not found")
        assert isinstance(exc, FileOperationError)
        assert isinstance(exc, MoneyPrinterError)

    def test_browser_errors(self):
        """Test browser error hierarchy."""
        exc = BrowserInitializationError("Failed to start browser")
        assert isinstance(exc, BrowserError)
        assert isinstance(exc, MoneyPrinterError)

        exc = ElementNotFoundError("Button not found")
        assert isinstance(exc, BrowserError)

    def test_video_errors(self):
        """Test video processing error hierarchy."""
        exc = VideoProcessingError("Processing failed")
        assert isinstance(exc, MoneyPrinterError)

    def test_validation_errors(self):
        """Test validation error hierarchy."""
        exc = ValidationError("Validation failed")
        assert isinstance(exc, MoneyPrinterError)


class TestLogException:
    """Test exception logging utility."""

    def test_log_standard_exception(self, caplog):
        """Test logging standard exceptions."""
        import logging

        exc = ValueError("Invalid value")
        log_exception(exc, level=logging.ERROR)

        assert "ValueError: Invalid value" in caplog.text

    def test_log_money_printer_exception(self, caplog):
        """Test logging MoneyPrinterError exceptions."""
        import logging

        exc = APIConnectionError("Failed to connect", endpoint="https://api.example.com")
        log_exception(exc, level=logging.ERROR)

        assert "Failed to connect" in caplog.text
        assert "endpoint=https://api.example.com" in caplog.text

    def test_log_with_custom_logger(self, caplog):
        """Test logging with custom logger."""
        import logging

        logger = logging.getLogger("test_logger")
        exc = ConfigurationError("Config error")

        log_exception(exc, logger=logger, level=logging.WARNING)

        assert "Config error" in caplog.text
        # Check it used the custom logger
        for record in caplog.records:
            if "Config error" in record.message:
                assert record.levelno == logging.WARNING

    def test_log_without_traceback(self, caplog):
        """Test logging without traceback."""
        import logging

        # Capture INFO level logs
        caplog.set_level(logging.INFO)

        exc = ValueError("Test error")
        log_exception(exc, level=logging.INFO, include_traceback=False)

        # Message should be logged
        assert "ValueError: Test error" in caplog.text


class TestExceptionCatchAll:
    """Test that all custom exceptions can be caught by MoneyPrinterError."""

    def test_catch_all_exceptions(self):
        """Test catching all custom exceptions with base class."""
        exceptions_to_test = [
            MissingConfigError("test"),
            APIConnectionError("test"),
            FileNotFoundError("test"),
            BrowserError("test"),
            VideoProcessingError("test"),
            ValidationError("test"),
        ]

        for exc in exceptions_to_test:
            try:
                raise exc
            except MoneyPrinterError as e:
                assert isinstance(e, MoneyPrinterError)
                assert str(e) == "test"
