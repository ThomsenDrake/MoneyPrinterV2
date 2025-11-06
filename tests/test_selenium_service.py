"""
Tests for Selenium Service abstraction layer.

This module tests the SeleniumService class which provides a high-level
interface for Selenium operations.
"""

from unittest.mock import MagicMock, Mock, call, patch

import pytest
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By

from src.exceptions import BrowserOperationError, ElementNotFoundError
from src.exceptions import TimeoutError as AppTimeoutError
from src.selenium_service import SeleniumService


class TestSeleniumServiceInit:
    """Tests for SeleniumService initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        mock_driver = Mock()
        service = SeleniumService(mock_driver)

        assert service.driver is mock_driver
        assert service.default_timeout == 10  # DEFAULT_WAIT_TIMEOUT from constants

    def test_init_with_custom_timeout(self):
        """Test initialization with custom timeout."""
        mock_driver = Mock()
        service = SeleniumService(mock_driver, default_timeout=30)

        assert service.driver is mock_driver
        assert service.default_timeout == 30


class TestSeleniumServiceNavigation:
    """Tests for navigation methods."""

    def test_navigate_to_success(self):
        """Test successful navigation to URL."""
        mock_driver = Mock()
        service = SeleniumService(mock_driver)

        service.navigate_to("https://example.com")

        mock_driver.get.assert_called_once_with("https://example.com")

    def test_navigate_to_failure(self):
        """Test navigation failure raises BrowserOperationError."""
        mock_driver = Mock()
        mock_driver.get.side_effect = Exception("Network error")
        service = SeleniumService(mock_driver)

        with pytest.raises(BrowserOperationError) as exc_info:
            service.navigate_to("https://example.com")

        assert "Navigation failed" in str(exc_info.value)


class TestSeleniumServiceWaitForElement:
    """Tests for wait_for_element method."""

    @patch("src.selenium_service.WebDriverWait")
    def test_wait_for_element_presence(self, mock_wait):
        """Test waiting for element presence."""
        mock_driver = Mock()
        mock_element = Mock()
        mock_wait_instance = Mock()
        mock_wait_instance.until.return_value = mock_element
        mock_wait.return_value = mock_wait_instance

        service = SeleniumService(mock_driver, default_timeout=10)
        element = service.wait_for_element(By.ID, "test-id", condition="presence")

        assert element is mock_element
        mock_wait.assert_called_once_with(mock_driver, 10)

    @patch("src.selenium_service.WebDriverWait")
    def test_wait_for_element_clickable(self, mock_wait):
        """Test waiting for element to be clickable."""
        mock_driver = Mock()
        mock_element = Mock()
        mock_wait_instance = Mock()
        mock_wait_instance.until.return_value = mock_element
        mock_wait.return_value = mock_wait_instance

        service = SeleniumService(mock_driver)
        element = service.wait_for_element(By.XPATH, "//button", condition="clickable", timeout=15)

        assert element is mock_element
        mock_wait.assert_called_once_with(mock_driver, 15)

    @patch("src.selenium_service.WebDriverWait")
    def test_wait_for_element_timeout(self, mock_wait):
        """Test timeout raises AppTimeoutError."""
        mock_driver = Mock()
        mock_wait_instance = Mock()
        mock_wait_instance.until.side_effect = TimeoutException()
        mock_wait.return_value = mock_wait_instance

        service = SeleniumService(mock_driver)

        with pytest.raises(AppTimeoutError) as exc_info:
            service.wait_for_element(By.ID, "missing-element")

        assert "Element not found within" in str(exc_info.value)

    def test_wait_for_element_invalid_condition(self):
        """Test invalid condition raises ValueError."""
        mock_driver = Mock()
        service = SeleniumService(mock_driver)

        with pytest.raises(ValueError) as exc_info:
            service.wait_for_element(By.ID, "test", condition="invalid")

        assert "Invalid condition" in str(exc_info.value)


class TestSeleniumServiceWaitForElements:
    """Tests for wait_for_elements method."""

    @patch("src.selenium_service.WebDriverWait")
    def test_wait_for_elements_success(self, mock_wait):
        """Test waiting for multiple elements."""
        mock_driver = Mock()
        mock_elements = [Mock(), Mock(), Mock()]
        mock_wait_instance = Mock()
        mock_wait_instance.until.return_value = mock_elements
        mock_wait.return_value = mock_wait_instance

        service = SeleniumService(mock_driver)
        elements = service.wait_for_elements(By.CLASS_NAME, "item")

        assert len(elements) == 3
        assert elements is mock_elements


class TestSeleniumServiceClickElement:
    """Tests for click_element method."""

    @patch("src.selenium_service.SeleniumService.wait_for_element")
    def test_click_element_success(self, mock_wait):
        """Test successful element click."""
        mock_driver = Mock()
        mock_element = Mock()
        mock_wait.return_value = mock_element

        service = SeleniumService(mock_driver)
        service.click_element(By.ID, "submit-button")

        mock_wait.assert_called_once_with(By.ID, "submit-button", None, "clickable")
        mock_element.click.assert_called_once()

    @patch("src.selenium_service.SeleniumService.wait_for_element")
    def test_click_element_no_wait_clickable(self, mock_wait):
        """Test clicking element without waiting for clickable."""
        mock_driver = Mock()
        mock_element = Mock()
        mock_wait.return_value = mock_element

        service = SeleniumService(mock_driver)
        service.click_element(By.ID, "button", wait_clickable=False)

        mock_wait.assert_called_once_with(By.ID, "button", None, "presence")


class TestSeleniumServiceSendKeys:
    """Tests for send_keys_to_element method."""

    @patch("src.selenium_service.SeleniumService.wait_for_element")
    def test_send_keys_with_clear(self, mock_wait):
        """Test sending keys with clear."""
        mock_driver = Mock()
        mock_element = Mock()
        mock_wait.return_value = mock_element

        service = SeleniumService(mock_driver)
        service.send_keys_to_element(By.ID, "input-field", "test text")

        mock_element.clear.assert_called_once()
        mock_element.send_keys.assert_called_once_with("test text")

    @patch("src.selenium_service.SeleniumService.wait_for_element")
    def test_send_keys_without_clear(self, mock_wait):
        """Test sending keys without clear."""
        mock_driver = Mock()
        mock_element = Mock()
        mock_wait.return_value = mock_element

        service = SeleniumService(mock_driver)
        service.send_keys_to_element(By.ID, "input-field", "test text", clear_first=False)

        mock_element.clear.assert_not_called()
        mock_element.send_keys.assert_called_once_with("test text")


class TestSeleniumServiceGetters:
    """Tests for getter methods."""

    @patch("src.selenium_service.SeleniumService.wait_for_element")
    def test_get_element_text(self, mock_wait):
        """Test getting element text."""
        mock_driver = Mock()
        mock_element = Mock()
        mock_element.text = "Element text content"
        mock_wait.return_value = mock_element

        service = SeleniumService(mock_driver)
        text = service.get_element_text(By.ID, "content")

        assert text == "Element text content"

    @patch("src.selenium_service.SeleniumService.wait_for_element")
    def test_get_element_attribute(self, mock_wait):
        """Test getting element attribute."""
        mock_driver = Mock()
        mock_element = Mock()
        mock_element.get_attribute.return_value = "https://example.com"
        mock_wait.return_value = mock_element

        service = SeleniumService(mock_driver)
        href = service.get_element_attribute(By.TAG_NAME, "a", "href")

        assert href == "https://example.com"
        mock_element.get_attribute.assert_called_once_with("href")


class TestSeleniumServiceWaitForURL:
    """Tests for wait_for_url_contains method."""

    @patch("src.selenium_service.WebDriverWait")
    def test_wait_for_url_contains_success(self, mock_wait):
        """Test waiting for URL to contain fragment."""
        mock_driver = Mock()
        mock_wait_instance = Mock()
        mock_wait_instance.until.return_value = True
        mock_wait.return_value = mock_wait_instance

        service = SeleniumService(mock_driver)
        result = service.wait_for_url_contains("/dashboard")

        assert result is True

    @patch("src.selenium_service.WebDriverWait")
    def test_wait_for_url_contains_timeout(self, mock_wait):
        """Test timeout when waiting for URL."""
        mock_driver = Mock()
        mock_driver.current_url = "https://example.com/login"
        mock_wait_instance = Mock()
        mock_wait_instance.until.side_effect = TimeoutException()
        mock_wait.return_value = mock_wait_instance

        service = SeleniumService(mock_driver)

        with pytest.raises(AppTimeoutError) as exc_info:
            service.wait_for_url_contains("/dashboard")

        assert "URL did not contain" in str(exc_info.value)


class TestSeleniumServiceUtilities:
    """Tests for utility methods."""

    @patch("src.selenium_service.SeleniumService.wait_for_element")
    def test_element_exists_true(self, mock_wait):
        """Test element_exists returns True when element exists."""
        mock_driver = Mock()
        mock_element = Mock()
        mock_wait.return_value = mock_element

        service = SeleniumService(mock_driver)
        exists = service.element_exists(By.ID, "existing-element")

        assert exists is True

    @patch("src.selenium_service.SeleniumService.wait_for_element")
    def test_element_exists_false(self, mock_wait):
        """Test element_exists returns False when element doesn't exist."""
        mock_driver = Mock()
        mock_wait.side_effect = AppTimeoutError("Not found")

        service = SeleniumService(mock_driver)
        exists = service.element_exists(By.ID, "missing-element")

        assert exists is False

    def test_get_current_url(self):
        """Test getting current URL."""
        mock_driver = Mock()
        mock_driver.current_url = "https://example.com/page"

        service = SeleniumService(mock_driver)
        url = service.get_current_url()

        assert url == "https://example.com/page"

    def test_execute_script(self):
        """Test JavaScript execution."""
        mock_driver = Mock()
        mock_driver.execute_script.return_value = "script result"

        service = SeleniumService(mock_driver)
        result = service.execute_script("return document.title;")

        assert result == "script result"
        mock_driver.execute_script.assert_called_once()


class TestSeleniumServiceCleanup:
    """Tests for cleanup methods."""

    def test_close(self):
        """Test closing browser window."""
        mock_driver = Mock()
        service = SeleniumService(mock_driver)

        service.close()

        mock_driver.close.assert_called_once()

    def test_quit(self):
        """Test quitting browser."""
        mock_driver = Mock()
        service = SeleniumService(mock_driver)

        service.quit()

        mock_driver.quit.assert_called_once()

    def test_switch_to_window(self):
        """Test switching to window."""
        mock_driver = Mock()
        mock_driver.switch_to = Mock()

        service = SeleniumService(mock_driver)
        service.switch_to_window("window-handle-123")

        mock_driver.switch_to.window.assert_called_once_with("window-handle-123")
