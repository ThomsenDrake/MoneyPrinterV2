"""
HTTP Client with connection pooling and retry logic.

This module provides a centralized HTTP client service that:
- Uses requests.Session for connection pooling
- Implements retry logic for transient failures
- Provides a consistent interface for HTTP requests

Eliminates code duplication and improves performance by reusing connections.
"""

import logging
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from urllib3.util.retry import Retry as URLRetry

from constants import DEFAULT_POOL_CONNECTIONS, DEFAULT_POOL_MAXSIZE


class HTTPClient:
    """
    Centralized HTTP client with connection pooling and retry logic.

    This class uses requests.Session for connection pooling, which reuses
    TCP connections and improves performance for multiple requests.

    The client is implemented as a singleton to maximize connection reuse.
    """

    _instance: Optional["HTTPClient"] = None
    _session: Optional[requests.Session] = None

    def __new__(cls):
        """Ensure only one HTTPClient instance exists (singleton pattern)."""
        if cls._instance is None:
            cls._instance = super(HTTPClient, cls).__new__(cls)
            cls._instance._initialize_session()
        return cls._instance

    def _initialize_session(self) -> None:
        """
        Initialize the requests session with connection pooling and retry strategy.

        Configures:
        - Connection pooling (max 10 connections per host)
        - Automatic retries for connection errors (3 attempts)
        - Backoff strategy for rate limiting
        """
        self._session = requests.Session()

        # Configure retry strategy for connection-level errors
        # This is separate from the application-level retry in _make_request_with_retry
        retry_strategy = URLRetry(
            total=3,  # Total number of retries
            backoff_factor=1,  # Exponential backoff: 1s, 2s, 4s
            status_forcelist=[429, 500, 502, 503, 504],  # Retry on these HTTP status codes
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE"],
        )

        # Mount adapter with retry strategy for both HTTP and HTTPS
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=DEFAULT_POOL_CONNECTIONS,  # Number of connection pools
            pool_maxsize=DEFAULT_POOL_MAXSIZE,  # Max connections per pool
        )

        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)

        logging.info("HTTP client initialized with connection pooling")

    @property
    def session(self) -> requests.Session:
        """
        Get the requests session.

        Returns:
            requests.Session: The configured session instance
        """
        if self._session is None:
            self._initialize_session()
        return self._session

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.RequestException, requests.Timeout)),
        reraise=True,
    )
    def request(
        self,
        method: str,
        url: str,
        timeout: int = 30,
        **kwargs,
    ) -> requests.Response:
        """
        Make HTTP request with automatic retry on transient failures.

        Uses the session's connection pool for improved performance.

        Args:
            method (str): HTTP method (GET, POST, PUT, DELETE, etc.)
            url (str): URL to request
            timeout (int): Request timeout in seconds (default: 30)
            **kwargs: Additional arguments for requests (headers, json, data, etc.)

        Returns:
            requests.Response: The response object

        Raises:
            requests.RequestException: If all retry attempts fail
            requests.Timeout: If the request times out

        Example:
            >>> client = HTTPClient()
            >>> response = client.request("GET", "https://api.example.com/data")
            >>> print(response.json())
        """
        logging.info(f"Making {method} request to {url}")

        response = self.session.request(method, url, timeout=timeout, **kwargs)
        response.raise_for_status()

        logging.debug(f"Request successful: {method} {url} - Status {response.status_code}")
        return response

    def get(self, url: str, **kwargs) -> requests.Response:
        """
        Make a GET request.

        Args:
            url (str): URL to request
            **kwargs: Additional arguments for requests

        Returns:
            requests.Response: The response object
        """
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        """
        Make a POST request.

        Args:
            url (str): URL to request
            **kwargs: Additional arguments for requests (json, data, etc.)

        Returns:
            requests.Response: The response object
        """
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs) -> requests.Response:
        """
        Make a PUT request.

        Args:
            url (str): URL to request
            **kwargs: Additional arguments for requests

        Returns:
            requests.Response: The response object
        """
        return self.request("PUT", url, **kwargs)

    def delete(self, url: str, **kwargs) -> requests.Response:
        """
        Make a DELETE request.

        Args:
            url (str): URL to request
            **kwargs: Additional arguments for requests

        Returns:
            requests.Response: The response object
        """
        return self.request("DELETE", url, **kwargs)

    def close(self) -> None:
        """
        Close the session and release connections.

        Should be called when the application is shutting down.
        """
        if self._session:
            self._session.close()
            logging.info("HTTP client session closed")

    @classmethod
    def reset_instance(cls) -> None:
        """
        Reset the singleton instance.

        Useful for testing and cleanup.
        """
        if cls._instance and cls._instance._session:
            cls._instance._session.close()
        cls._instance = None
        logging.debug("HTTPClient instance reset")


# Convenience function to get the global HTTP client
def get_http_client() -> HTTPClient:
    """
    Get the global HTTP client instance.

    Returns:
        HTTPClient: The singleton HTTP client instance

    Example:
        >>> from http_client import get_http_client
        >>> client = get_http_client()
        >>> response = client.get("https://api.example.com/data")
    """
    return HTTPClient()
