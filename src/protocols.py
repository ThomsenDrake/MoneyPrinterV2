"""
Protocol interfaces for dependency injection and abstraction layers.

This module defines the contracts (interfaces) for various components in the
MoneyPrinterV2 application. Using Protocol classes enables:
- Dependency injection
- Easy mocking for tests
- Loose coupling between components
- Adherence to SOLID principles
"""

from typing import Any, Dict, List, Optional, Protocol


class BrowserProtocol(Protocol):
    """
    Protocol defining the interface for browser automation.

    This protocol abstracts Selenium WebDriver operations, allowing for
    easy testing and potential replacement with other automation frameworks.
    """

    def get(self, url: str) -> None:
        """
        Navigate to the specified URL.

        Args:
            url: The URL to navigate to
        """
        ...

    def quit(self) -> None:
        """Close the browser and clean up resources."""
        ...

    def find_element(self, by: str, value: str) -> Any:
        """
        Find a single element on the page.

        Args:
            by: The locator strategy (e.g., By.ID, By.XPATH)
            value: The locator value

        Returns:
            The found element

        Raises:
            NoSuchElementException: If element is not found
        """
        ...

    def find_elements(self, by: str, value: str) -> List[Any]:
        """
        Find multiple elements on the page.

        Args:
            by: The locator strategy
            value: The locator value

        Returns:
            List of found elements (empty list if none found)
        """
        ...


class HTTPClientProtocol(Protocol):
    """
    Protocol for HTTP client operations.

    This protocol abstracts HTTP requests, enabling connection pooling,
    rate limiting, and easy mocking in tests.
    """

    def get(
        self, url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 30, **kwargs
    ) -> Any:
        """
        Perform an HTTP GET request.

        Args:
            url: The URL to request
            headers: Optional HTTP headers
            timeout: Request timeout in seconds
            **kwargs: Additional arguments passed to the underlying implementation

        Returns:
            Response object

        Raises:
            HTTPError: If request fails
        """
        ...

    def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 30,
        **kwargs,
    ) -> Any:
        """
        Perform an HTTP POST request.

        Args:
            url: The URL to request
            data: Form data to send
            json: JSON data to send
            headers: Optional HTTP headers
            timeout: Request timeout in seconds
            **kwargs: Additional arguments passed to the underlying implementation

        Returns:
            Response object

        Raises:
            HTTPError: If request fails
        """
        ...


class ConfigProviderProtocol(Protocol):
    """
    Protocol for configuration access.

    This protocol abstracts configuration retrieval, enabling different
    configuration sources (JSON, environment variables, remote config).
    """

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: The configuration key
            default: Default value if key is not found

        Returns:
            The configuration value or default
        """
        ...

    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration values.

        Returns:
            Dictionary of all configuration values
        """
        ...


class LLMServiceProtocol(Protocol):
    """
    Protocol for Large Language Model services.

    This protocol abstracts LLM interactions, enabling easy swapping
    between different LLM providers (Mistral, OpenAI, Claude, etc.).
    """

    def generate_response(
        self, prompt: str, model: Optional[str] = None, **kwargs
    ) -> str:
        """
        Generate a response from the LLM.

        Args:
            prompt: The input prompt
            model: Optional model identifier
            **kwargs: Additional provider-specific parameters

        Returns:
            The generated text response

        Raises:
            LLMError: If generation fails
        """
        ...


class CacheProtocol(Protocol):
    """
    Protocol for caching operations.

    This protocol abstracts cache storage, enabling different
    cache backends (file, Redis, in-memory, etc.).
    """

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from cache.

        Args:
            key: The cache key

        Returns:
            The cached value or None if not found
        """
        ...

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Store a value in cache.

        Args:
            key: The cache key
            value: The value to cache
            ttl: Optional time-to-live in seconds
        """
        ...

    def delete(self, key: str) -> None:
        """
        Delete a value from cache.

        Args:
            key: The cache key
        """
        ...

    def exists(self, key: str) -> bool:
        """
        Check if a key exists in cache.

        Args:
            key: The cache key

        Returns:
            True if key exists, False otherwise
        """
        ...


class StorageProtocol(Protocol):
    """
    Protocol for file storage operations.

    This protocol abstracts file operations, enabling different
    storage backends (local filesystem, S3, Google Cloud Storage).
    """

    def save(self, path: str, content: Any) -> None:
        """
        Save content to storage.

        Args:
            path: The file path
            content: The content to save
        """
        ...

    def load(self, path: str) -> Any:
        """
        Load content from storage.

        Args:
            path: The file path

        Returns:
            The loaded content

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        ...

    def exists(self, path: str) -> bool:
        """
        Check if a file exists.

        Args:
            path: The file path

        Returns:
            True if file exists, False otherwise
        """
        ...

    def delete(self, path: str) -> None:
        """
        Delete a file from storage.

        Args:
            path: The file path
        """
        ...


class BrowserFactoryProtocol(Protocol):
    """
    Protocol for browser factory operations.

    This protocol abstracts browser creation, enabling different
    browser types and configurations.
    """

    def create_browser(
        self, profile_path: str, headless: bool = False, **kwargs
    ) -> BrowserProtocol:
        """
        Create a browser instance.

        Args:
            profile_path: Path to the browser profile
            headless: Whether to run in headless mode
            **kwargs: Additional browser-specific configuration

        Returns:
            A configured browser instance

        Raises:
            BrowserCreationError: If browser creation fails
        """
        ...
