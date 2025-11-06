"""Tests for error handling decorators and utilities."""

import logging
import time

import pytest

from src.error_handlers import (
    ErrorContext,
    fallback_on_error,
    handle_errors,
    log_errors,
    retry_on_failure,
    safe_return,
    validate_not_none,
)
from src.exceptions import APIError


class TestRetryOnFailure:
    """Test the retry_on_failure decorator."""

    def test_successful_call_no_retry(self):
        """Test that successful calls don't retry."""
        call_count = []

        @retry_on_failure(max_attempts=3)
        def success_func():
            call_count.append(1)
            return "success"

        result = success_func()
        assert result == "success"
        assert len(call_count) == 1  # Only called once

    def test_retry_on_failure(self):
        """Test that failed calls are retried."""
        call_count = []

        @retry_on_failure(max_attempts=3, delay=0.01)
        def failing_func():
            call_count.append(1)
            if len(call_count) < 3:
                raise ValueError("Not yet")
            return "success"

        result = failing_func()
        assert result == "success"
        assert len(call_count) == 3  # Retried 2 times, succeeded on 3rd

    def test_retry_exhausted(self):
        """Test that exhausted retries raise exception."""

        @retry_on_failure(max_attempts=3, delay=0.01)
        def always_fails():
            raise ValueError("Always fails")

        with pytest.raises(ValueError, match="Always fails"):
            always_fails()

    def test_retry_with_specific_exceptions(self):
        """Test retry only catches specified exceptions."""

        @retry_on_failure(max_attempts=3, delay=0.01, exceptions=(ValueError,))
        def raises_wrong_exception():
            raise TypeError("Wrong exception type")

        with pytest.raises(TypeError):
            raises_wrong_exception()

    def test_exponential_backoff(self):
        """Test that retry uses exponential backoff."""
        call_times = []

        @retry_on_failure(max_attempts=3, delay=0.1, backoff=2.0)
        def timing_test():
            call_times.append(time.time())
            if len(call_times) < 3:
                raise ValueError("Retry")
            return "done"

        timing_test()

        # Check delays are approximately exponential (0.1s, 0.2s)
        if len(call_times) >= 3:
            delay1 = call_times[1] - call_times[0]
            delay2 = call_times[2] - call_times[1]
            assert delay1 >= 0.09  # ~0.1s with some tolerance
            assert delay2 >= 0.18  # ~0.2s with some tolerance


class TestHandleErrors:
    """Test the handle_errors decorator."""

    def test_successful_call(self):
        """Test successful calls pass through."""

        @handle_errors()
        def success_func():
            return "success"

        result = success_func()
        assert result == "success"

    def test_error_reraised_by_default(self):
        """Test errors are re-raised by default."""

        @handle_errors()
        def failing_func():
            raise ValueError("Error")

        with pytest.raises(ValueError, match="Error"):
            failing_func()

    def test_error_return_default(self):
        """Test returning default value on error."""

        @handle_errors(default_return="default", reraise=False)
        def failing_func():
            raise ValueError("Error")

        result = failing_func()
        assert result == "default"

    def test_error_logged(self, caplog):
        """Test errors are logged."""

        @handle_errors(reraise=False, log_level=logging.WARNING)
        def failing_func():
            raise ValueError("Test error")

        failing_func()
        assert "Test error" in caplog.text

    def test_specific_exceptions_only(self):
        """Test only specified exceptions are handled."""

        @handle_errors(reraise=False, exceptions=(ValueError,))
        def raises_type_error():
            raise TypeError("Not handled")

        with pytest.raises(TypeError):
            raises_type_error()


class TestSafeReturn:
    """Test the safe_return decorator."""

    def test_returns_default_on_error(self):
        """Test safe_return returns default on error."""

        @safe_return(default=[])
        def failing_func():
            raise ValueError("Error")

        result = failing_func()
        assert result == []

    def test_successful_return(self):
        """Test safe_return passes through successful results."""

        @safe_return(default=None)
        def success_func():
            return "result"

        result = success_func()
        assert result == "result"

    def test_logs_errors(self, caplog):
        """Test safe_return logs errors."""
        # Capture WARNING level logs (default for safe_return)
        caplog.set_level(logging.WARNING)

        @safe_return(default=0, log_level=logging.WARNING)
        def failing_func():
            raise ValueError("Safe error")

        failing_func()
        assert "Safe error" in caplog.text


class TestLogErrors:
    """Test the log_errors decorator."""

    def test_logs_and_reraises(self, caplog):
        """Test log_errors logs and re-raises."""

        @log_errors()
        def failing_func():
            raise ValueError("Logged error")

        with pytest.raises(ValueError, match="Logged error"):
            failing_func()

        assert "Logged error" in caplog.text

    def test_successful_call_no_log(self, caplog):
        """Test successful calls don't log."""

        @log_errors()
        def success_func():
            return "success"

        result = success_func()
        assert result == "success"
        assert len(caplog.records) == 0


class TestValidateNotNone:
    """Test the validate_not_none decorator."""

    def test_valid_arguments(self):
        """Test valid (non-None) arguments pass through."""

        @validate_not_none("api_key", "endpoint")
        def api_call(api_key, endpoint, timeout=30):
            return f"{api_key}:{endpoint}"

        result = api_call("key123", "https://api.example.com")
        assert result == "key123:https://api.example.com"

    def test_none_argument_raises(self):
        """Test None argument raises ValueError."""

        @validate_not_none("api_key")
        def api_call(api_key):
            return api_key

        with pytest.raises(ValueError, match="api_key.*cannot be None"):
            api_call(None)

    def test_validation_with_kwargs(self):
        """Test validation works with keyword arguments."""

        @validate_not_none("required_param")
        def func_with_kwargs(required_param, optional=None):
            return required_param

        # Valid call
        assert func_with_kwargs("value") == "value"

        # Invalid call
        with pytest.raises(ValueError, match="required_param.*cannot be None"):
            func_with_kwargs(None)

    def test_validation_multiple_params(self):
        """Test validation of multiple parameters."""

        @validate_not_none("param1", "param2", "param3")
        def multi_param(param1, param2, param3):
            return f"{param1}:{param2}:{param3}"

        # All valid
        assert multi_param("a", "b", "c") == "a:b:c"

        # First None
        with pytest.raises(ValueError, match="param1"):
            multi_param(None, "b", "c")

        # Middle None
        with pytest.raises(ValueError, match="param2"):
            multi_param("a", None, "c")

        # Last None
        with pytest.raises(ValueError, match="param3"):
            multi_param("a", "b", None)


class TestFallbackOnError:
    """Test the fallback_on_error decorator."""

    def test_successful_call_no_fallback(self):
        """Test successful calls don't use fallback."""

        def fallback_func():
            return "fallback"

        @fallback_on_error(fallback_func)
        def primary_func():
            return "primary"

        result = primary_func()
        assert result == "primary"

    def test_error_uses_fallback(self):
        """Test errors trigger fallback function."""

        def fallback_func():
            return "fallback"

        @fallback_on_error(fallback_func)
        def failing_func():
            raise ValueError("Error")

        result = failing_func()
        assert result == "fallback"

    def test_fallback_with_arguments(self):
        """Test fallback receives same arguments."""

        def fallback_func(x, y):
            return x + y + 100  # Different calculation

        @fallback_on_error(fallback_func)
        def primary_func(x, y):
            raise ValueError("Error")

        result = primary_func(10, 20)
        assert result == 130  # 10 + 20 + 100

    def test_fallback_logs_message(self, caplog):
        """Test fallback logs message."""

        def fallback_func():
            return "fallback"

        @fallback_on_error(fallback_func, log_message="API unavailable")
        def failing_func():
            raise ValueError("Error")

        failing_func()
        assert "API unavailable" in caplog.text


class TestErrorContext:
    """Test the ErrorContext context manager."""

    def test_successful_operation(self):
        """Test successful operations don't trigger error handling."""
        with ErrorContext("Test operation") as ctx:
            ctx.set_result("success")

        assert ctx.result == "success"
        assert ctx.exception is None

    def test_error_reraised(self):
        """Test errors are re-raised by default."""
        with pytest.raises(ValueError, match="Test error"):
            with ErrorContext("Test operation", reraise=True):
                raise ValueError("Test error")

    def test_error_suppressed_with_default(self):
        """Test errors can be suppressed with default return."""
        with ErrorContext("Test operation", reraise=False, default_return="default") as ctx:
            raise ValueError("Error")

        assert ctx.result == "default"
        assert isinstance(ctx.exception, ValueError)

    def test_error_logged(self, caplog):
        """Test errors are logged."""
        with ErrorContext("Test operation", reraise=False):
            raise ValueError("Context error")

        assert "Context error" in caplog.text

    def test_context_with_result(self):
        """Test setting result in context."""
        with ErrorContext("Test operation", reraise=False) as ctx:
            result = "computed_value"
            ctx.set_result(result)

        assert ctx.result == "computed_value"


class TestIntegration:
    """Integration tests combining multiple decorators."""

    def test_retry_with_handle_errors(self):
        """Test combining retry_on_failure with handle_errors."""
        call_count = []

        @handle_errors(default_return="handled", reraise=False)
        @retry_on_failure(max_attempts=2, delay=0.01)
        def unstable_func():
            call_count.append(1)
            raise ValueError("Unstable")

        result = unstable_func()
        assert result == "handled"
        assert len(call_count) == 2  # Retried once

    def test_validate_with_safe_return(self):
        """Test combining validate_not_none with safe_return."""

        @safe_return(default=None)
        @validate_not_none("param")
        def validated_func(param):
            return param.upper()

        # Valid call
        assert validated_func("test") == "TEST"

        # Invalid call - safe_return catches validation error
        result = validated_func(None)
        assert result is None
