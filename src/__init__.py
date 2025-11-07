"""
MoneyPrinterV2 - Automated video generation and social media automation.

This package provides comprehensive automation for creating and managing content
across multiple platforms including YouTube, Twitter, and affiliate marketing.

Main Modules:
    - config: Configuration management
    - constants: Application-wide constants
    - exceptions: Custom exception hierarchy
    - protocols: Protocol interfaces for dependency injection

Core Services:
    - llm_service: LLM interaction wrapper
    - selenium_service: Browser automation abstraction
    - http_client: HTTP client with connection pooling
    - scheduler_service: Task scheduling
    - account_manager: Account management
    - llm_cache: LLM response caching

Infrastructure:
    - cache: File-based caching with locking
    - logger: Logging configuration
    - validation: Input validation
    - error_handlers: Reusable error handling decorators
    - rate_limiter: API rate limiting

Platform Integrations:
    - classes.YouTube: YouTube automation
    - classes.Twitter: Twitter automation
    - classes.AFM: Affiliate marketing
    - classes.Outreach: Outreach automation
    - classes.Tts: Text-to-speech

Utilities:
    - utils: General utility functions
    - browser_factory: Browser instance creation
    - health_checks: API health validation

Entry Points:
    - main: Interactive CLI application
    - cron: Scheduled automation
"""

__version__ = "2.0.0"
__author__ = "MoneyPrinterV2 Contributors"

# Note: We don't eagerly import modules to avoid loading dependencies
# Users should import directly as needed
__all__ = [
    # Version info
    "__version__",
    "__author__",
]
