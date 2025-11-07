Core Modules
============

The core modules provide fundamental functionality including configuration,
constants, and application entry points.

Configuration Management
------------------------

.. automodule:: config
   :members:
   :undoc-members:
   :show-inheritance:

Configuration Schema
--------------------

.. automodule:: config_schema
   :members:
   :undoc-members:
   :show-inheritance:

Constants
---------

.. automodule:: constants
   :members:
   :undoc-members:
   :show-inheritance:

Exceptions
----------

.. automodule:: exceptions
   :members:
   :undoc-members:
   :show-inheritance:

Exception Hierarchy
~~~~~~~~~~~~~~~~~~~

All custom exceptions inherit from ``MoneyPrinterError``:

.. code-block:: text

   MoneyPrinterError (base)
   ├── ConfigurationError
   │   ├── MissingConfigError
   │   └── InvalidConfigError
   ├── APIError
   │   ├── APIConnectionError
   │   ├── APIAuthenticationError
   │   ├── APIRateLimitError
   │   └── APIResponseError
   ├── FileOperationError
   │   ├── FileNotFoundError
   │   ├── FilePermissionError
   │   ├── FileLockError
   │   └── CacheError
   ├── BrowserError
   │   ├── BrowserInitializationError
   │   ├── ElementNotFoundError
   │   ├── BrowserTimeoutError
   │   └── BrowserOperationError
   ├── TimeoutError
   ├── VideoProcessingError
   │   ├── ImageGenerationError
   │   ├── AudioGenerationError
   │   └── VideoRenderError
   ├── AccountError
   │   ├── AccountNotFoundError
   │   └── DuplicateAccountError
   └── ValidationError
       └── InputValidationError

Main Application
----------------

.. automodule:: main
   :members:
   :undoc-members:
   :show-inheritance:

Cron Scheduler
--------------

.. automodule:: cron
   :members:
   :undoc-members:
   :show-inheritance:
