"""
Tests for Protocol interfaces.

This module tests that our protocol definitions are properly structured
and can be used for type checking and dependency injection.
"""

from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, Mock

import pytest

from src.protocols import (
    BrowserFactoryProtocol,
    BrowserProtocol,
    CacheProtocol,
    ConfigProviderProtocol,
    HTTPClientProtocol,
    LLMServiceProtocol,
    StorageProtocol,
)


class TestBrowserProtocol:
    """Tests for BrowserProtocol interface."""

    def test_browser_protocol_with_mock(self):
        """Test that a mock object satisfies BrowserProtocol."""
        # Create a mock browser
        mock_browser = Mock(spec=BrowserProtocol)
        mock_browser.get = Mock()
        mock_browser.quit = Mock()
        mock_browser.find_element = Mock(return_value=Mock())
        mock_browser.find_elements = Mock(return_value=[Mock(), Mock()])

        # Test that protocol methods work
        mock_browser.get("https://example.com")
        mock_browser.get.assert_called_once_with("https://example.com")

        element = mock_browser.find_element("id", "test")
        assert element is not None

        elements = mock_browser.find_elements("class", "test")
        assert len(elements) == 2

        mock_browser.quit()
        mock_browser.quit.assert_called_once()


class TestHTTPClientProtocol:
    """Tests for HTTPClientProtocol interface."""

    def test_http_client_protocol_with_mock(self):
        """Test that a mock object satisfies HTTPClientProtocol."""
        mock_client = Mock(spec=HTTPClientProtocol)
        mock_response = Mock(status_code=200, text="OK")
        mock_client.get = Mock(return_value=mock_response)
        mock_client.post = Mock(return_value=mock_response)

        # Test GET
        response = mock_client.get("https://api.example.com", headers={"Auth": "token"})
        assert response.status_code == 200
        mock_client.get.assert_called_once()

        # Test POST
        response = mock_client.post(
            "https://api.example.com", json={"key": "value"}, headers={"Auth": "token"}
        )
        assert response.status_code == 200
        mock_client.post.assert_called_once()


class TestConfigProviderProtocol:
    """Tests for ConfigProviderProtocol interface."""

    def test_config_provider_protocol_with_mock(self):
        """Test that a mock object satisfies ConfigProviderProtocol."""
        mock_config = Mock(spec=ConfigProviderProtocol)
        mock_config.get.side_effect = lambda k, default=None: {"api_key": "test123"}.get(
            k, default
        )
        mock_config.get_all = Mock(return_value={"api_key": "test123", "timeout": 30})

        # Test get with default
        value = mock_config.get("api_key", default="default")
        assert value == "test123"

        value = mock_config.get("missing_key", default="default_value")
        assert value == "default_value"

        # Test get_all
        all_config = mock_config.get_all()
        assert "api_key" in all_config
        assert all_config["api_key"] == "test123"


class TestLLMServiceProtocol:
    """Tests for LLMServiceProtocol interface."""

    def test_llm_service_protocol_with_mock(self):
        """Test that a mock object satisfies LLMServiceProtocol."""
        mock_llm = Mock(spec=LLMServiceProtocol)
        mock_llm.generate_response = Mock(return_value="Generated text response")

        # Test generate_response
        response = mock_llm.generate_response("Test prompt", model="test-model")
        assert response == "Generated text response"
        mock_llm.generate_response.assert_called_once_with("Test prompt", model="test-model")


class TestCacheProtocol:
    """Tests for CacheProtocol interface."""

    def test_cache_protocol_with_mock(self):
        """Test that a mock object satisfies CacheProtocol."""
        mock_cache = Mock(spec=CacheProtocol)
        mock_cache.get = Mock(return_value="cached_value")
        mock_cache.set = Mock()
        mock_cache.delete = Mock()
        mock_cache.exists = Mock(return_value=True)

        # Test get
        value = mock_cache.get("key1")
        assert value == "cached_value"

        # Test set
        mock_cache.set("key2", "value2", ttl=3600)
        mock_cache.set.assert_called_once_with("key2", "value2", ttl=3600)

        # Test delete
        mock_cache.delete("key1")
        mock_cache.delete.assert_called_once_with("key1")

        # Test exists
        exists = mock_cache.exists("key1")
        assert exists is True


class TestStorageProtocol:
    """Tests for StorageProtocol interface."""

    def test_storage_protocol_with_mock(self):
        """Test that a mock object satisfies StorageProtocol."""
        mock_storage = Mock(spec=StorageProtocol)
        mock_storage.save = Mock()
        mock_storage.load = Mock(return_value="file content")
        mock_storage.exists = Mock(return_value=True)
        mock_storage.delete = Mock()

        # Test save
        mock_storage.save("/path/to/file", "content")
        mock_storage.save.assert_called_once_with("/path/to/file", "content")

        # Test load
        content = mock_storage.load("/path/to/file")
        assert content == "file content"

        # Test exists
        exists = mock_storage.exists("/path/to/file")
        assert exists is True

        # Test delete
        mock_storage.delete("/path/to/file")
        mock_storage.delete.assert_called_once_with("/path/to/file")


class TestBrowserFactoryProtocol:
    """Tests for BrowserFactoryProtocol interface."""

    def test_browser_factory_protocol_with_mock(self):
        """Test that a mock object satisfies BrowserFactoryProtocol."""
        mock_factory = Mock(spec=BrowserFactoryProtocol)
        mock_browser = Mock(spec=BrowserProtocol)
        mock_factory.create_browser = Mock(return_value=mock_browser)

        # Test create_browser
        browser = mock_factory.create_browser("/path/to/profile", headless=True)
        assert browser is mock_browser
        mock_factory.create_browser.assert_called_once_with("/path/to/profile", headless=True)


class TestProtocolInteroperability:
    """Tests for protocol interoperability and dependency injection."""

    def test_protocols_enable_dependency_injection(self):
        """Test that protocols enable clean dependency injection."""

        # Example class that accepts protocol interfaces
        class VideoGenerator:
            def __init__(
                self,
                browser: BrowserProtocol,
                http_client: HTTPClientProtocol,
                llm_service: LLMServiceProtocol,
                cache: CacheProtocol,
            ):
                self.browser = browser
                self.http_client = http_client
                self.llm_service = llm_service
                self.cache = cache

            def generate(self):
                # Check cache first
                cached = self.cache.get("script")
                if cached:
                    return cached

                # Generate new content
                script = self.llm_service.generate_response("Generate a script")
                self.cache.set("script", script)
                return script

        # Create mock dependencies
        mock_browser = Mock(spec=BrowserProtocol)
        mock_http = Mock(spec=HTTPClientProtocol)
        mock_llm = Mock(spec=LLMServiceProtocol)
        mock_llm.generate_response = Mock(return_value="New script")
        mock_cache = Mock(spec=CacheProtocol)
        mock_cache.get = Mock(return_value=None)
        mock_cache.set = Mock()

        # Inject dependencies
        generator = VideoGenerator(
            browser=mock_browser, http_client=mock_http, llm_service=mock_llm, cache=mock_cache
        )

        # Test that dependencies work correctly
        script = generator.generate()
        assert script == "New script"
        mock_cache.get.assert_called_once_with("script")
        mock_llm.generate_response.assert_called_once()
        mock_cache.set.assert_called_once_with("script", "New script")

    def test_protocols_enable_easy_testing(self):
        """Test that protocols make testing easier."""

        # Another example showing testability
        def fetch_and_cache_data(http_client: HTTPClientProtocol, cache: CacheProtocol, url: str):
            """Function that uses protocol interfaces."""
            # Check cache
            cached = cache.get(url)
            if cached:
                return cached

            # Fetch from HTTP
            response = http_client.get(url)
            data = response.text

            # Cache the result
            cache.set(url, data, ttl=3600)
            return data

        # Create mocks
        mock_http = Mock(spec=HTTPClientProtocol)
        mock_response = Mock(text="Response data")
        mock_http.get = Mock(return_value=mock_response)
        mock_cache = Mock(spec=CacheProtocol)
        mock_cache.get = Mock(return_value=None)
        mock_cache.set = Mock()

        # Test the function
        result = fetch_and_cache_data(mock_http, mock_cache, "https://example.com")
        assert result == "Response data"
        mock_http.get.assert_called_once_with("https://example.com")
        mock_cache.set.assert_called_once()
