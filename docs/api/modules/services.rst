Service Modules
===============

Service modules provide high-level abstractions for external integrations
and complex operations.

LLM Service
-----------

The LLM Service provides a clean interface for interacting with Large Language Models,
with built-in caching and error handling.

.. automodule:: llm_service
   :members:
   :undoc-members:
   :show-inheritance:

LLM Cache
~~~~~~~~~

.. automodule:: llm_cache
   :members:
   :undoc-members:
   :show-inheritance:

Selenium Service
----------------

The Selenium Service provides a high-level abstraction over Selenium WebDriver
with 20+ convenience methods for common browser automation tasks.

.. automodule:: selenium_service
   :members:
   :undoc-members:
   :show-inheritance:

Scheduler Service
-----------------

Centralized task scheduling with CRON-like functionality.

.. automodule:: scheduler_service
   :members:
   :undoc-members:
   :show-inheritance:

Account Manager
---------------

Multi-account management with rotation and state tracking.

.. automodule:: account_manager
   :members:
   :undoc-members:
   :show-inheritance:

Browser Factory
---------------

Factory pattern for creating and configuring browser instances.

.. automodule:: browser_factory
   :members:
   :undoc-members:
   :show-inheritance:

Protocols
---------

Protocol interfaces for dependency injection and loose coupling.

.. automodule:: protocols
   :members:
   :undoc-members:
   :show-inheritance:

Protocol Hierarchy
~~~~~~~~~~~~~~~~~~

The following protocols define contracts for dependency injection:

- ``ConfigProtocol``: Configuration access interface
- ``CacheProtocol``: Caching operations interface
- ``SeleniumProtocol``: Browser automation interface
- ``LLMProtocol``: LLM interaction interface
- ``HTTPProtocol``: HTTP client interface
- ``LoggerProtocol``: Logging interface
- ``ValidationProtocol``: Input validation interface

Usage Example:

.. code-block:: python

   from protocols import SeleniumProtocol
   from selenium_service import SeleniumService

   class MyAutomation:
       def __init__(self, selenium: SeleniumProtocol):
           self.selenium = selenium

   # Inject concrete implementation
   service = SeleniumService(browser)
   automation = MyAutomation(selenium=service)
