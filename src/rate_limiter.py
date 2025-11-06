"""
Rate limiting utilities for API calls.

This module provides decorators and classes for rate limiting API calls
to prevent exceeding provider quotas and avoid 429 Too Many Requests errors.
"""

import logging
import time
from collections import defaultdict
from functools import wraps
from threading import Lock
from typing import Callable, Dict, Optional

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Thread-safe rate limiter using token bucket algorithm.

    The token bucket algorithm allows bursts of requests up to max_calls,
    then enforces a steady rate of max_calls per period.
    """

    def __init__(self, max_calls: int, period: float):
        """
        Initialize rate limiter.

        Args:
            max_calls: Maximum number of calls allowed in the time period
            period: Time period in seconds
        """
        self.max_calls = max_calls
        self.period = period
        self.calls: Dict[str, list] = defaultdict(list)
        self.lock = Lock()

    def __call__(self, key: str = "default") -> bool:
        """
        Check if a call is allowed under rate limiting.

        Args:
            key: Identifier for the rate limit (e.g., API endpoint, user ID)

        Returns:
            True if call is allowed, False if rate limit exceeded
        """
        with self.lock:
            now = time.time()

            # Remove calls outside the current period
            self.calls[key] = [
                call_time for call_time in self.calls[key] if now - call_time < self.period
            ]

            # Check if we can make another call
            if len(self.calls[key]) < self.max_calls:
                self.calls[key].append(now)
                return True

            return False

    def wait_for_token(self, key: str = "default", timeout: Optional[float] = None) -> bool:
        """
        Wait until a token is available (call is allowed).

        Args:
            key: Identifier for the rate limit
            timeout: Maximum time to wait in seconds (None = wait forever)

        Returns:
            True if token acquired, False if timeout occurred
        """
        start_time = time.time()

        while True:
            if self(key):
                return True

            if timeout is not None and (time.time() - start_time) >= timeout:
                logger.warning(f"Rate limiter timeout after {timeout}s for key: {key}")
                return False

            # Calculate sleep time until next token available
            with self.lock:
                if self.calls[key]:
                    oldest_call = min(self.calls[key])
                    sleep_time = self.period - (time.time() - oldest_call)
                    if sleep_time > 0:
                        time.sleep(min(sleep_time, 1.0))
                else:
                    time.sleep(0.1)

    def get_remaining_calls(self, key: str = "default") -> int:
        """
        Get number of remaining calls allowed in current period.

        Args:
            key: Identifier for the rate limit

        Returns:
            Number of calls remaining
        """
        with self.lock:
            now = time.time()
            self.calls[key] = [
                call_time for call_time in self.calls[key] if now - call_time < self.period
            ]
            return max(0, self.max_calls - len(self.calls[key]))


# Pre-configured rate limiters for common APIs
class APIRateLimiters:
    """Pre-configured rate limiters for common API providers."""

    # Mistral AI: ~5 requests per second (conservative)
    MISTRAL_AI = RateLimiter(max_calls=5, period=1.0)

    # Venice AI: Conservative limit (adjust based on your tier)
    VENICE_AI = RateLimiter(max_calls=10, period=1.0)

    # AssemblyAI: Conservative limit (adjust based on your tier)
    ASSEMBLY_AI = RateLimiter(max_calls=5, period=1.0)

    # Generic HTTP: Generous limit for general HTTP requests
    GENERIC_HTTP = RateLimiter(max_calls=100, period=60.0)


def rate_limit(
    limiter: RateLimiter,
    key: Optional[str] = None,
    wait: bool = True,
    timeout: Optional[float] = 30.0,
) -> Callable:
    """
    Decorator to rate limit function calls.

    Args:
        limiter: RateLimiter instance to use
        key: Optional key for rate limiting (default: function name)
        wait: If True, wait for token; if False, raise exception immediately
        timeout: Maximum time to wait for token (None = wait forever)

    Returns:
        Decorated function

    Example:
        >>> @rate_limit(APIRateLimiters.MISTRAL_AI)
        ... def call_mistral_api(prompt: str) -> str:
        ...     return mistral_client.chat(prompt)

        >>> @rate_limit(APIRateLimiters.VENICE_AI, key="image_generation")
        ... def generate_image(prompt: str) -> bytes:
        ...     return venice_client.generate(prompt)
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Use function name as default key
            rate_limit_key = key or func.__name__

            if wait:
                # Wait for token to become available
                if not limiter.wait_for_token(rate_limit_key, timeout=timeout):
                    raise TimeoutError(
                        f"Rate limiter timeout after {timeout}s waiting for {rate_limit_key}"
                    )
            else:
                # Check immediately, raise if not allowed
                if not limiter(rate_limit_key):
                    remaining = limiter.get_remaining_calls(rate_limit_key)
                    raise RuntimeError(
                        f"Rate limit exceeded for {rate_limit_key}. "
                        f"Remaining calls: {remaining}/{limiter.max_calls}"
                    )

            # Log rate limiting information
            remaining = limiter.get_remaining_calls(rate_limit_key)
            logger.debug(f"API call: {rate_limit_key} | Remaining: {remaining}/{limiter.max_calls}")

            # Execute the function
            return func(*args, **kwargs)

        return wrapper

    return decorator


def get_rate_limiter_for_api(api_name: str) -> RateLimiter:
    """
    Get appropriate rate limiter for an API.

    Args:
        api_name: Name of the API (mistral, venice, assemblyai, http)

    Returns:
        RateLimiter instance

    Raises:
        ValueError: If API name is unknown
    """
    api_name_lower = api_name.lower()

    limiters = {
        "mistral": APIRateLimiters.MISTRAL_AI,
        "mistralai": APIRateLimiters.MISTRAL_AI,
        "venice": APIRateLimiters.VENICE_AI,
        "assemblyai": APIRateLimiters.ASSEMBLY_AI,
        "assembly": APIRateLimiters.ASSEMBLY_AI,
        "http": APIRateLimiters.GENERIC_HTTP,
        "generic": APIRateLimiters.GENERIC_HTTP,
    }

    limiter = limiters.get(api_name_lower)
    if limiter is None:
        raise ValueError(
            f"Unknown API: {api_name}. " f"Supported APIs: {', '.join(limiters.keys())}"
        )

    return limiter


# Example usage and testing
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.DEBUG)

    # Example 1: Using decorator with pre-configured limiter
    @rate_limit(APIRateLimiters.MISTRAL_AI)
    def call_mistral_api(prompt: str) -> str:
        print(f"Calling Mistral API with: {prompt}")
        return f"Response to: {prompt}"

    # Example 2: Using decorator with custom limiter
    custom_limiter = RateLimiter(max_calls=3, period=1.0)

    @rate_limit(custom_limiter, key="custom_api")
    def call_custom_api(data: str) -> str:
        print(f"Calling custom API with: {data}")
        return f"Result: {data}"

    # Example 3: Manual usage
    limiter = RateLimiter(max_calls=5, period=2.0)

    for i in range(10):
        if limiter.wait_for_token("test"):
            print(f"Request {i+1} allowed (remaining: {limiter.get_remaining_calls('test')})")
        else:
            print(f"Request {i+1} blocked")
