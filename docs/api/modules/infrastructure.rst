Infrastructure Modules
======================

Infrastructure modules provide low-level functionality like caching,
logging, HTTP communication, and error handling.

HTTP Client
-----------

HTTP client with connection pooling for improved performance.

.. automodule:: http_client
   :members:
   :undoc-members:
   :show-inheritance:

Features:
~~~~~~~~~

- Connection pooling with singleton pattern
- Automatic retry on failure
- Timeout configuration
- ~40% faster than creating new connections

Cache
-----

File-based caching with atomic locking to prevent race conditions.

.. automodule:: cache
   :members:
   :undoc-members:
   :show-inheritance:

Logger
------

Structured logging with file rotation and multiple output formats.

.. automodule:: logger
   :members:
   :undoc-members:
   :show-inheritance:

Rate Limiter
------------

Token bucket-based rate limiting for API calls.

.. automodule:: rate_limiter
   :members:
   :undoc-members:
   :show-inheritance:

Usage Example:

.. code-block:: python

   from rate_limiter import RateLimiter, rate_limit

   # Create rate limiter (10 requests per 60 seconds)
   limiter = RateLimiter(max_calls=10, period=60)

   # Use as context manager
   with limiter:
       make_api_call()

   # Or as decorator
   @rate_limit(max_calls=10, period=60)
   def api_function():
       return api_call()

Error Handlers
--------------

Reusable error handling decorators for common patterns.

.. automodule:: error_handlers
   :members:
   :undoc-members:
   :show-inheritance:

Available Decorators:
~~~~~~~~~~~~~~~~~~~~~

- ``@retry_on_failure``: Automatic retry with exponential backoff
- ``@handle_errors``: Consistent error logging and handling
- ``@safe_return``: Return default value on error
- ``@log_errors``: Log errors without changing behavior
- ``@validate_not_none``: Argument validation
- ``@fallback_on_error``: Fallback function support

Example:

.. code-block:: python

   from error_handlers import retry_on_failure, safe_return

   @retry_on_failure(max_attempts=3, delay=2.0)
   def fetch_data():
       return unstable_api_call()

   @safe_return(default=None)
   def get_optional_value():
       return potentially_failing_operation()

Validation
----------

Input validation and sanitization to prevent security issues.

.. automodule:: validation
   :members:
   :undoc-members:
   :show-inheritance:

Health Checks
-------------

API health validation for startup verification.

.. automodule:: health_checks
   :members:
   :undoc-members:
   :show-inheritance:
