"""
Tests for the HTTP client with connection pooling.
"""

import os

# Import the module under test
import sys
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from http_client import HTTPClient, get_http_client  # noqa: E402


class TestHTTPClient:
    """Test suite for the HTTPClient class."""

    def test_singleton_pattern(self):
        """Test that HTTPClient implements singleton pattern."""
        client1 = HTTPClient()
        client2 = HTTPClient()
        assert client1 is client2, "HTTPClient should return the same instance"

    def test_get_http_client(self):
        """Test get_http_client convenience function."""
        client = get_http_client()
        assert isinstance(client, HTTPClient)

    def test_session_initialized(self):
        """Test that session is properly initialized."""
        HTTPClient.reset_instance()
        client = HTTPClient()
        assert client.session is not None
        assert isinstance(client.session, requests.Session)

    @patch("http_client.requests.Session")
    def test_connection_pooling_configured(self, mock_session_class):
        """Test that connection pooling is properly configured."""
        HTTPClient.reset_instance()
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        client = HTTPClient()

        # Verify session mount was called for both http and https
        assert mock_session.mount.call_count >= 2

    @patch.object(requests.Session, "request")
    def test_request_method(self, mock_request):
        """Test that request method calls session.request correctly."""
        HTTPClient.reset_instance()
        client = HTTPClient()

        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        # Make request
        response = client.request("GET", "https://api.example.com/data")

        # Verify request was made
        mock_request.assert_called_once()
        assert response.status_code == 200

    @patch.object(requests.Session, "request")
    def test_get_convenience_method(self, mock_request):
        """Test GET convenience method."""
        HTTPClient.reset_instance()
        client = HTTPClient()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        client.get("https://api.example.com/data")

        # Verify GET method was used
        call_args = mock_request.call_args
        assert call_args[0][0] == "GET"

    @patch.object(requests.Session, "request")
    def test_post_convenience_method(self, mock_request):
        """Test POST convenience method."""
        HTTPClient.reset_instance()
        client = HTTPClient()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        client.post("https://api.example.com/data", json={"key": "value"})

        # Verify POST method was used
        call_args = mock_request.call_args
        assert call_args[0][0] == "POST"

    @patch.object(requests.Session, "request")
    def test_request_with_headers(self, mock_request):
        """Test request with custom headers."""
        HTTPClient.reset_instance()
        client = HTTPClient()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        headers = {"Authorization": "Bearer token123"}
        client.request("GET", "https://api.example.com/data", headers=headers)

        # Verify headers were passed
        call_args = mock_request.call_args
        assert "headers" in call_args[1]

    @patch.object(requests.Session, "request")
    def test_request_timeout(self, mock_request):
        """Test that timeout is set correctly."""
        HTTPClient.reset_instance()
        client = HTTPClient()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        client.request("GET", "https://api.example.com/data", timeout=60)

        # Verify timeout was set
        call_args = mock_request.call_args
        assert call_args[1]["timeout"] == 60

    @patch.object(requests.Session, "request")
    def test_request_raises_on_error(self, mock_request):
        """Test that request raises exception on HTTP error."""
        HTTPClient.reset_instance()
        client = HTTPClient()

        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status = Mock(side_effect=requests.HTTPError("404 Not Found"))
        mock_request.return_value = mock_response

        with pytest.raises(requests.HTTPError):
            client.request("GET", "https://api.example.com/not-found")

    @patch.object(requests.Session, "close")
    def test_close_method(self, mock_close):
        """Test that close method closes the session."""
        HTTPClient.reset_instance()
        mock_close.reset_mock()  # Reset mock after reset_instance() call

        client = HTTPClient()
        client.close()

        mock_close.assert_called_once()

    def test_reset_instance(self):
        """Test that reset_instance clears the singleton."""
        HTTPClient.reset_instance()
        client1 = HTTPClient()

        HTTPClient.reset_instance()
        client2 = HTTPClient()

        # After reset, instances should be different
        # (Note: Due to singleton pattern, this might need adjustment)
        assert HTTPClient._instance is None or client1 is not client2

    @patch.object(requests.Session, "request")
    def test_retry_on_failure(self, mock_request):
        """Test that request retries on transient failures."""
        HTTPClient.reset_instance()
        client = HTTPClient()

        # First call fails, second succeeds
        mock_response_fail = Mock()
        mock_response_fail.raise_for_status = Mock(
            side_effect=requests.RequestException("Connection error")
        )

        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.raise_for_status = Mock()

        mock_request.side_effect = [
            mock_response_fail,
            mock_response_success,
        ]

        # Should succeed after retry
        response = client.request("GET", "https://api.example.com/data")
        assert response.status_code == 200
        assert mock_request.call_count == 2


class TestHTTPClientIntegration:
    """Integration tests for HTTP client (these would typically use mock servers)."""

    @pytest.fixture(autouse=True)
    def reset_client(self):
        """Reset the client before each test."""
        HTTPClient.reset_instance()
        yield
        HTTPClient.reset_instance()

    @patch.object(requests.Session, "request")
    def test_multiple_requests_reuse_session(self, mock_request):
        """Test that multiple requests reuse the same session."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        client = get_http_client()

        # Make multiple requests
        client.get("https://api.example.com/1")
        client.get("https://api.example.com/2")
        client.post("https://api.example.com/3", json={})

        # All requests should use the same session
        assert mock_request.call_count == 3
