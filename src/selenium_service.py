"""
Selenium Service for abstracting common Selenium operations.

This module provides a high-level interface for Selenium WebDriver operations,
eliminating duplication and providing consistent error handling and logging.
"""

import logging
from typing import Any, List, Optional

from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from constants import DEFAULT_WAIT_TIMEOUT
from exceptions import (
    BrowserOperationError,
    ElementNotFoundError,
    TimeoutError as AppTimeoutError,
)


class SeleniumService:
    """
    Service class providing high-level Selenium operations.

    This class abstracts common Selenium patterns and provides:
    - Consistent error handling
    - Automatic waiting for elements
    - Logging of operations
    - Cleaner API for browser automation
    """

    def __init__(self, driver: WebDriver, default_timeout: int = DEFAULT_WAIT_TIMEOUT):
        """
        Initialize the Selenium service.

        Args:
            driver: The WebDriver instance to use
            default_timeout: Default timeout for wait operations in seconds
        """
        self.driver = driver
        self.default_timeout = default_timeout
        self.logger = logging.getLogger(__name__)

    def navigate_to(self, url: str) -> None:
        """
        Navigate to a URL with error handling.

        Args:
            url: The URL to navigate to

        Raises:
            BrowserOperationError: If navigation fails
        """
        try:
            self.logger.info(f"Navigating to: {url}")
            self.driver.get(url)
        except WebDriverException as e:
            self.logger.error(f"Failed to navigate to {url}: {str(e)}")
            raise BrowserOperationError(f"Navigation failed: {url}") from e

    def wait_for_element(
        self, by: By, value: str, timeout: Optional[int] = None, condition: str = "presence"
    ) -> WebElement:
        """
        Wait for an element to be present/visible/clickable.

        Args:
            by: The locator strategy (e.g., By.ID, By.XPATH)
            value: The locator value
            timeout: Optional timeout override (uses default if not provided)
            condition: The wait condition - "presence", "visible", or "clickable"

        Returns:
            The found element

        Raises:
            ElementNotFoundError: If element is not found within timeout
            AppTimeoutError: If operation times out
        """
        timeout = timeout or self.default_timeout

        try:
            # Select the appropriate expected condition
            if condition == "presence":
                ec_func = EC.presence_of_element_located
            elif condition == "visible":
                ec_func = EC.visibility_of_element_located
            elif condition == "clickable":
                ec_func = EC.element_to_be_clickable
            else:
                raise ValueError(
                    f"Invalid condition: {condition}. Use 'presence', 'visible', or 'clickable'"
                )

            self.logger.debug(
                f"Waiting for element ({condition}): {by}='{value}' (timeout: {timeout}s)"
            )

            element = WebDriverWait(self.driver, timeout).until(ec_func((by, value)))

            self.logger.debug(f"Element found: {by}='{value}'")
            return element

        except TimeoutException as e:
            self.logger.error(f"Timeout waiting for element: {by}='{value}' ({timeout}s)")
            raise AppTimeoutError(
                f"Element not found within {timeout}s: {by}='{value}'"
            ) from e
        except NoSuchElementException as e:
            self.logger.error(f"Element not found: {by}='{value}'")
            raise ElementNotFoundError(f"Element not found: {by}='{value}'") from e

    def wait_for_elements(
        self, by: By, value: str, timeout: Optional[int] = None
    ) -> List[WebElement]:
        """
        Wait for multiple elements to be present.

        Args:
            by: The locator strategy
            value: The locator value
            timeout: Optional timeout override

        Returns:
            List of found elements

        Raises:
            AppTimeoutError: If elements are not found within timeout
        """
        timeout = timeout or self.default_timeout

        try:
            self.logger.debug(f"Waiting for elements: {by}='{value}' (timeout: {timeout}s)")

            elements = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_all_elements_located((by, value))
            )

            self.logger.debug(f"Found {len(elements)} elements: {by}='{value}'")
            return elements

        except TimeoutException as e:
            self.logger.error(f"Timeout waiting for elements: {by}='{value}' ({timeout}s)")
            raise AppTimeoutError(
                f"Elements not found within {timeout}s: {by}='{value}'"
            ) from e

    def click_element(
        self, by: By, value: str, timeout: Optional[int] = None, wait_clickable: bool = True
    ) -> None:
        """
        Wait for an element and click it.

        Args:
            by: The locator strategy
            value: The locator value
            timeout: Optional timeout override
            wait_clickable: Whether to wait for element to be clickable (default: True)

        Raises:
            ElementNotFoundError: If element is not found
            BrowserOperationError: If click fails
        """
        try:
            condition = "clickable" if wait_clickable else "presence"
            element = self.wait_for_element(by, value, timeout, condition)

            self.logger.debug(f"Clicking element: {by}='{value}'")
            element.click()
            self.logger.debug(f"Clicked element: {by}='{value}'")

        except Exception as e:
            self.logger.error(f"Failed to click element {by}='{value}': {str(e)}")
            raise BrowserOperationError(f"Click failed: {by}='{value}'") from e

    def send_keys_to_element(
        self, by: By, value: str, text: str, timeout: Optional[int] = None, clear_first: bool = True
    ) -> None:
        """
        Wait for an element and send keys to it.

        Args:
            by: The locator strategy
            value: The locator value
            text: The text to send
            timeout: Optional timeout override
            clear_first: Whether to clear the element before sending keys (default: True)

        Raises:
            ElementNotFoundError: If element is not found
            BrowserOperationError: If sending keys fails
        """
        try:
            element = self.wait_for_element(by, value, timeout, "visible")

            if clear_first:
                self.logger.debug(f"Clearing element: {by}='{value}'")
                element.clear()

            self.logger.debug(f"Sending keys to element: {by}='{value}'")
            element.send_keys(text)
            self.logger.debug(f"Sent keys to element: {by}='{value}'")

        except Exception as e:
            self.logger.error(f"Failed to send keys to element {by}='{value}': {str(e)}")
            raise BrowserOperationError(f"Send keys failed: {by}='{value}'") from e

    def get_element_text(self, by: By, value: str, timeout: Optional[int] = None) -> str:
        """
        Wait for an element and get its text.

        Args:
            by: The locator strategy
            value: The locator value
            timeout: Optional timeout override

        Returns:
            The element's text content

        Raises:
            ElementNotFoundError: If element is not found
        """
        element = self.wait_for_element(by, value, timeout, "visible")
        text = element.text
        self.logger.debug(f"Got text from element {by}='{value}': '{text[:50]}...'")
        return text

    def get_element_attribute(
        self, by: By, value: str, attribute: str, timeout: Optional[int] = None
    ) -> Optional[str]:
        """
        Wait for an element and get one of its attributes.

        Args:
            by: The locator strategy
            value: The locator value
            attribute: The attribute name to retrieve
            timeout: Optional timeout override

        Returns:
            The attribute value or None if not found

        Raises:
            ElementNotFoundError: If element is not found
        """
        element = self.wait_for_element(by, value, timeout)
        attr_value = element.get_attribute(attribute)
        self.logger.debug(
            f"Got attribute '{attribute}' from element {by}='{value}': '{attr_value}'"
        )
        return attr_value

    def wait_for_url_contains(self, url_fragment: str, timeout: Optional[int] = None) -> bool:
        """
        Wait for the current URL to contain a specific fragment.

        Args:
            url_fragment: The URL fragment to wait for
            timeout: Optional timeout override

        Returns:
            True if URL contains fragment within timeout

        Raises:
            AppTimeoutError: If timeout is reached
        """
        timeout = timeout or self.default_timeout

        try:
            self.logger.debug(f"Waiting for URL to contain: '{url_fragment}' (timeout: {timeout}s)")

            WebDriverWait(self.driver, timeout).until(EC.url_contains(url_fragment))

            self.logger.debug(f"URL now contains: '{url_fragment}'")
            return True

        except TimeoutException as e:
            current_url = self.driver.current_url
            self.logger.error(
                f"Timeout waiting for URL to contain '{url_fragment}'. Current URL: {current_url}"
            )
            raise AppTimeoutError(
                f"URL did not contain '{url_fragment}' within {timeout}s. Current: {current_url}"
            ) from e

    def element_exists(self, by: By, value: str, timeout: int = 2) -> bool:
        """
        Check if an element exists without throwing an exception.

        Args:
            by: The locator strategy
            value: The locator value
            timeout: Timeout for the check in seconds (default: 2)

        Returns:
            True if element exists, False otherwise
        """
        try:
            self.wait_for_element(by, value, timeout)
            return True
        except (ElementNotFoundError, AppTimeoutError):
            return False

    def get_current_url(self) -> str:
        """
        Get the current URL.

        Returns:
            The current URL
        """
        url = self.driver.current_url
        self.logger.debug(f"Current URL: {url}")
        return url

    def execute_script(self, script: str, *args) -> Any:
        """
        Execute JavaScript in the browser.

        Args:
            script: The JavaScript code to execute
            *args: Arguments to pass to the script

        Returns:
            The return value of the script

        Raises:
            BrowserOperationError: If script execution fails
        """
        try:
            self.logger.debug(f"Executing script: {script[:100]}...")
            result = self.driver.execute_script(script, *args)
            return result
        except WebDriverException as e:
            self.logger.error(f"Script execution failed: {str(e)}")
            raise BrowserOperationError(f"Script execution failed: {script[:50]}...") from e

    def switch_to_window(self, window_handle: str) -> None:
        """
        Switch to a different browser window.

        Args:
            window_handle: The window handle to switch to

        Raises:
            BrowserOperationError: If window switch fails
        """
        try:
            self.logger.debug(f"Switching to window: {window_handle}")
            self.driver.switch_to.window(window_handle)
        except WebDriverException as e:
            self.logger.error(f"Failed to switch to window {window_handle}: {str(e)}")
            raise BrowserOperationError(f"Window switch failed: {window_handle}") from e

    def close(self) -> None:
        """Close the current browser window."""
        try:
            self.logger.info("Closing browser window")
            self.driver.close()
        except WebDriverException as e:
            self.logger.warning(f"Error closing browser window: {str(e)}")

    def quit(self) -> None:
        """Quit the browser and clean up resources."""
        try:
            self.logger.info("Quitting browser")
            self.driver.quit()
        except WebDriverException as e:
            self.logger.warning(f"Error quitting browser: {str(e)}")
