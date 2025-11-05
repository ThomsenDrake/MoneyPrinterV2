"""
Browser Factory for creating and managing Selenium browser instances.

This module eliminates code duplication across YouTube, Twitter, and AFM classes
by centralizing browser initialization logic.
"""
import logging
from typing import Optional
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager


class BrowserFactory:
    """
    Factory class for creating Selenium Firefox browser instances.

    This class centralizes Firefox browser initialization, which was previously
    duplicated across YouTube, Twitter, and AffiliateMarketing classes.
    """

    @staticmethod
    def create_firefox_browser(
        profile_path: str,
        headless: bool = False,
        use_profile_object: bool = True
    ) -> webdriver.Firefox:
        """
        Create a Firefox browser instance with the specified configuration.

        Args:
            profile_path: Path to the Firefox profile directory
            headless: Whether to run browser in headless mode (default: False)
            use_profile_object: Whether to use FirefoxProfile object (True) or
                              add_argument approach (False). Default True for
                              backward compatibility with YouTube class.

        Returns:
            Configured Firefox WebDriver instance

        Raises:
            Exception: If browser creation fails

        Example:
            >>> browser = BrowserFactory.create_firefox_browser(
            ...     "/path/to/profile",
            ...     headless=True
            ... )
        """
        try:
            options = Options()

            # Set headless mode if requested
            if headless:
                options.add_argument("--headless")
                logging.info("Browser set to headless mode")

            # Configure profile using the specified method
            if use_profile_object:
                # Method used by YouTube class
                profile = webdriver.FirefoxProfile(profile_path)
                options.profile = profile
                logging.info(f"Using FirefoxProfile object for: {profile_path}")
            else:
                # Method used by Twitter and AFM classes
                options.add_argument("-profile")
                options.add_argument(profile_path)
                logging.info(f"Using profile argument for: {profile_path}")

            # Set up the service with GeckoDriver
            service = Service(GeckoDriverManager().install())

            # Create and return the browser instance
            browser = webdriver.Firefox(service=service, options=options)
            logging.info("Firefox browser created successfully")

            return browser

        except Exception as e:
            logging.error(f"Failed to create Firefox browser: {str(e)}", exc_info=True)
            raise


class BrowserContextManager:
    """
    Context manager for safely managing browser lifecycle.

    This ensures that browser instances are properly cleaned up even if
    exceptions occur during usage.

    Example:
        >>> with BrowserContextManager("/path/to/profile") as browser:
        ...     browser.get("https://example.com")
        ...     # browser automatically closed on exit
    """

    def __init__(
        self,
        profile_path: str,
        headless: bool = False,
        use_profile_object: bool = True
    ):
        """
        Initialize the browser context manager.

        Args:
            profile_path: Path to the Firefox profile directory
            headless: Whether to run browser in headless mode
            use_profile_object: Whether to use FirefoxProfile object
        """
        self.profile_path = profile_path
        self.headless = headless
        self.use_profile_object = use_profile_object
        self.browser: Optional[webdriver.Firefox] = None

    def __enter__(self) -> webdriver.Firefox:
        """Create and return the browser instance."""
        self.browser = BrowserFactory.create_firefox_browser(
            profile_path=self.profile_path,
            headless=self.headless,
            use_profile_object=self.use_profile_object
        )
        return self.browser

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up browser instance on context exit."""
        if self.browser:
            try:
                self.browser.quit()
                logging.info("Browser closed successfully")
            except Exception as e:
                logging.warning(f"Error closing browser: {str(e)}")

        # Don't suppress exceptions
        return False
