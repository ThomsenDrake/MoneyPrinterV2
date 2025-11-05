"""
Pytest configuration and shared fixtures for MoneyPrinterV2 tests.
"""
import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_config_data():
    """Return mock configuration data for testing."""
    return {
        "verbose": True,
        "headless": False,
        "firefox_profile": "/path/to/firefox/profile",
        "mistral_api_key": "test-mistral-key",
        "venice_api_key": "test-venice-key",
        "assembly_ai_api_key": "test-assemblyai-key",
        "ai_model": "mistral-large-latest",
        "automation_platform": "both",
        "song_directory": "/path/to/songs",
        "font": "/path/to/font.ttf",
        "scraper_timeout": 300,
        "n_threads": 4,
        "email": {
            "username": "test@example.com",
            "password": "test-password"
        }
    }


@pytest.fixture
def mock_config_file(temp_dir, mock_config_data):
    """Create a temporary config.json file."""
    config_path = temp_dir / "config.json"
    with open(config_path, 'w') as f:
        json.dump(mock_config_data, f, indent=4)
    return config_path


@pytest.fixture
def mock_cache_data():
    """Return mock cache data for testing."""
    return {
        "test_niche": {
            "hook": "Test Hook",
            "topics": ["Topic 1", "Topic 2", "Topic 3"],
            "next_index": 1
        }
    }


@pytest.fixture
def mock_cache_file(temp_dir, mock_cache_data):
    """Create a temporary cache.json file."""
    cache_path = temp_dir / "cache.json"
    with open(cache_path, 'w') as f:
        json.dump(mock_cache_data, f, indent=4)
    return cache_path


@pytest.fixture
def mock_selenium_browser():
    """Create a mock Selenium WebDriver browser."""
    browser = MagicMock()
    browser.quit = Mock()
    browser.get = Mock()
    browser.find_element = Mock()
    browser.find_elements = Mock(return_value=[])
    return browser


@pytest.fixture
def mock_mistral_client():
    """Create a mock Mistral AI client."""
    client = MagicMock()

    # Mock chat response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Mocked AI response"

    client.chat.return_value = mock_response
    return client


@pytest.fixture
def mock_requests(monkeypatch):
    """Mock requests library for HTTP calls."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"success": True}
    mock_response.content = b"mock content"

    mock_get = Mock(return_value=mock_response)
    mock_post = Mock(return_value=mock_response)

    monkeypatch.setattr("requests.get", mock_get)
    monkeypatch.setattr("requests.post", mock_post)

    return {
        "get": mock_get,
        "post": mock_post,
        "response": mock_response
    }


@pytest.fixture(autouse=True)
def reset_config_singleton():
    """Reset ConfigManager singleton between tests."""
    # This will be implemented when we test the ConfigManager
    yield
    # Reset singleton state after each test
    from config import ConfigManager
    ConfigManager._instance = None
    ConfigManager._config = None
