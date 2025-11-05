"""
Unit tests for BrowserFactory (src/browser_factory.py).
"""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest


class TestBrowserFactory:
    """Tests for BrowserFactory class."""

    @patch("browser_factory.webdriver.Firefox")
    @patch("browser_factory.Service")
    @patch("browser_factory.GeckoDriverManager")
    @patch("browser_factory.Options")
    @patch("browser_factory.webdriver.FirefoxProfile")
    def test_create_firefox_browser_with_profile_object(
        self,
        mock_profile_class,
        mock_options_class,
        mock_gecko_manager,
        mock_service_class,
        mock_firefox,
    ):
        """Test creating Firefox browser with FirefoxProfile object."""
        from browser_factory import BrowserFactory

        # Setup mocks
        mock_options = MagicMock()
        mock_options_class.return_value = mock_options

        mock_profile = MagicMock()
        mock_profile_class.return_value = mock_profile

        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        mock_gecko_manager.return_value.install.return_value = "/path/to/geckodriver"

        mock_browser = MagicMock()
        mock_firefox.return_value = mock_browser

        # Create browser
        result = BrowserFactory.create_firefox_browser(
            profile_path="/path/to/profile", headless=False, use_profile_object=True
        )

        # Verify behavior
        mock_profile_class.assert_called_once_with("/path/to/profile")
        assert mock_options.profile == mock_profile
        mock_firefox.assert_called_once_with(service=mock_service, options=mock_options)
        assert result == mock_browser

    @patch("browser_factory.webdriver.Firefox")
    @patch("browser_factory.Service")
    @patch("browser_factory.GeckoDriverManager")
    @patch("browser_factory.Options")
    def test_create_firefox_browser_with_profile_argument(
        self, mock_options_class, mock_gecko_manager, mock_service_class, mock_firefox
    ):
        """Test creating Firefox browser with profile argument."""
        from browser_factory import BrowserFactory

        # Setup mocks
        mock_options = MagicMock()
        mock_options_class.return_value = mock_options

        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        mock_gecko_manager.return_value.install.return_value = "/path/to/geckodriver"

        mock_browser = MagicMock()
        mock_firefox.return_value = mock_browser

        # Create browser
        result = BrowserFactory.create_firefox_browser(
            profile_path="/path/to/profile", headless=False, use_profile_object=False
        )

        # Verify behavior
        assert mock_options.add_argument.call_count == 2
        mock_options.add_argument.assert_any_call("-profile")
        mock_options.add_argument.assert_any_call("/path/to/profile")
        mock_firefox.assert_called_once_with(service=mock_service, options=mock_options)
        assert result == mock_browser

    @patch("browser_factory.webdriver.Firefox")
    @patch("browser_factory.Service")
    @patch("browser_factory.GeckoDriverManager")
    @patch("browser_factory.Options")
    @patch("browser_factory.webdriver.FirefoxProfile")
    def test_create_firefox_browser_headless(
        self,
        mock_profile_class,
        mock_options_class,
        mock_gecko_manager,
        mock_service_class,
        mock_firefox,
    ):
        """Test creating Firefox browser in headless mode."""
        from browser_factory import BrowserFactory

        # Setup mocks
        mock_options = MagicMock()
        mock_options_class.return_value = mock_options

        mock_profile = MagicMock()
        mock_profile_class.return_value = mock_profile

        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        mock_gecko_manager.return_value.install.return_value = "/path/to/geckodriver"

        mock_browser = MagicMock()
        mock_firefox.return_value = mock_browser

        # Create browser with headless=True
        result = BrowserFactory.create_firefox_browser(
            profile_path="/path/to/profile", headless=True, use_profile_object=True
        )

        # Verify headless argument was added
        mock_options.add_argument.assert_called_with("--headless")
        assert result == mock_browser

    @patch("browser_factory.webdriver.Firefox")
    @patch("browser_factory.webdriver.FirefoxProfile")
    @patch("browser_factory.Service")
    @patch("browser_factory.GeckoDriverManager")
    @patch("browser_factory.Options")
    def test_create_firefox_browser_exception(
        self, mock_options_class, mock_gecko_manager, mock_service_class, mock_profile_class, mock_firefox
    ):
        """Test handling exception during browser creation."""
        from browser_factory import BrowserFactory

        # Setup mocks - profile should succeed but Firefox creation should fail
        mock_profile = MagicMock()
        mock_profile_class.return_value = mock_profile
        mock_firefox.side_effect = Exception("Browser creation failed")

        # Verify exception is raised
        with pytest.raises(Exception, match="Browser creation failed"):
            BrowserFactory.create_firefox_browser(profile_path="/path/to/profile", headless=False)

    @patch("browser_factory.GeckoDriverManager")
    def test_geckodriver_manager_called(self, mock_gecko_manager):
        """Test that GeckoDriverManager is called to install driver."""
        from browser_factory import BrowserFactory

        mock_gecko_manager.return_value.install.return_value = "/path/to/driver"

        with patch("browser_factory.webdriver.Firefox"):
            with patch("browser_factory.Options"):
                with patch("browser_factory.webdriver.FirefoxProfile"):
                    BrowserFactory.create_firefox_browser(profile_path="/path/to/profile")

        mock_gecko_manager.return_value.install.assert_called_once()


class TestBrowserContextManager:
    """Tests for BrowserContextManager class."""

    @patch("browser_factory.BrowserFactory.create_firefox_browser")
    def test_context_manager_creates_browser(self, mock_create_browser):
        """Test that context manager creates browser on entry."""
        from browser_factory import BrowserContextManager

        mock_browser = MagicMock()
        mock_create_browser.return_value = mock_browser

        with BrowserContextManager("/path/to/profile") as browser:
            assert browser == mock_browser
            mock_create_browser.assert_called_once_with(
                profile_path="/path/to/profile", headless=False, use_profile_object=True
            )

    @patch("browser_factory.BrowserFactory.create_firefox_browser")
    def test_context_manager_closes_browser(self, mock_create_browser):
        """Test that context manager closes browser on exit."""
        from browser_factory import BrowserContextManager

        mock_browser = MagicMock()
        mock_create_browser.return_value = mock_browser

        with BrowserContextManager("/path/to/profile") as browser:
            pass  # Just enter and exit

        mock_browser.quit.assert_called_once()

    @patch("browser_factory.BrowserFactory.create_firefox_browser")
    def test_context_manager_closes_browser_on_exception(self, mock_create_browser):
        """Test that context manager closes browser even if exception occurs."""
        from browser_factory import BrowserContextManager

        mock_browser = MagicMock()
        mock_create_browser.return_value = mock_browser

        with pytest.raises(ValueError):
            with BrowserContextManager("/path/to/profile") as browser:
                raise ValueError("Test exception")

        # Browser should still be closed
        mock_browser.quit.assert_called_once()

    @patch("browser_factory.BrowserFactory.create_firefox_browser")
    def test_context_manager_with_headless(self, mock_create_browser):
        """Test context manager with headless mode."""
        from browser_factory import BrowserContextManager

        mock_browser = MagicMock()
        mock_create_browser.return_value = mock_browser

        with BrowserContextManager("/path/to/profile", headless=True) as browser:
            pass

        mock_create_browser.assert_called_once_with(
            profile_path="/path/to/profile", headless=True, use_profile_object=True
        )

    @patch("browser_factory.BrowserFactory.create_firefox_browser")
    def test_context_manager_with_profile_argument(self, mock_create_browser):
        """Test context manager with profile argument method."""
        from browser_factory import BrowserContextManager

        mock_browser = MagicMock()
        mock_create_browser.return_value = mock_browser

        with BrowserContextManager("/path/to/profile", use_profile_object=False) as browser:
            pass

        mock_create_browser.assert_called_once_with(
            profile_path="/path/to/profile", headless=False, use_profile_object=False
        )

    @patch("browser_factory.BrowserFactory.create_firefox_browser")
    def test_context_manager_handles_quit_exception(self, mock_create_browser):
        """Test that context manager handles exception during quit."""
        from browser_factory import BrowserContextManager

        mock_browser = MagicMock()
        mock_browser.quit.side_effect = Exception("Quit failed")
        mock_create_browser.return_value = mock_browser

        # Should not raise exception, just log warning
        with BrowserContextManager("/path/to/profile") as browser:
            pass

    @patch("browser_factory.BrowserFactory.create_firefox_browser")
    def test_context_manager_does_not_suppress_exceptions(self, mock_create_browser):
        """Test that context manager doesn't suppress user exceptions."""
        from browser_factory import BrowserContextManager

        mock_browser = MagicMock()
        mock_create_browser.return_value = mock_browser

        with pytest.raises(RuntimeError, match="User exception"):
            with BrowserContextManager("/path/to/profile") as browser:
                raise RuntimeError("User exception")

    @patch("browser_factory.BrowserFactory.create_firefox_browser")
    def test_context_manager_parameters(self, mock_create_browser):
        """Test that context manager passes all parameters correctly."""
        from browser_factory import BrowserContextManager

        mock_browser = MagicMock()
        mock_create_browser.return_value = mock_browser

        manager = BrowserContextManager(
            profile_path="/custom/profile", headless=True, use_profile_object=False
        )

        assert manager.profile_path == "/custom/profile"
        assert manager.headless is True
        assert manager.use_profile_object is False

        with manager as browser:
            pass

        mock_create_browser.assert_called_once_with(
            profile_path="/custom/profile", headless=True, use_profile_object=False
        )
