MoneyPrinterV2 API Documentation
=================================

Welcome to MoneyPrinterV2's API documentation. This project provides comprehensive
automation for creating and managing content across multiple platforms including
YouTube, Twitter, and affiliate marketing.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules/core
   modules/services
   modules/infrastructure
   modules/platforms
   modules/utilities

Quick Links
-----------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Overview
--------

MoneyPrinterV2 is an enterprise-grade automation framework that provides:

- **Video Generation**: Automated YouTube video creation with AI-generated scripts
- **Social Media Automation**: Twitter posting and engagement
- **Affiliate Marketing**: Automated affiliate campaign management
- **Account Management**: Multi-account handling with rotation
- **AI Integration**: LLM-powered content generation with caching
- **Browser Automation**: Selenium-based web automation

Key Features
~~~~~~~~~~~~

- ✅ **Type Safety**: ~95% type hint coverage with mypy validation
- ✅ **Testing**: ~60% test coverage with 495+ tests
- ✅ **Security**: Environment-based secrets management, input validation
- ✅ **Performance**: Connection pooling, response caching, parallel processing
- ✅ **Error Handling**: Comprehensive exception hierarchy with retry logic
- ✅ **Dependency Injection**: Protocol-based abstractions for loose coupling

Architecture
~~~~~~~~~~~~

The codebase follows a layered architecture:

1. **Core Layer** (config, constants, main)
   - Configuration management
   - Application entry points
   - Core business logic

2. **Service Layer** (services)
   - LLMService: AI/LLM interactions
   - SeleniumService: Browser automation
   - SchedulerService: Task scheduling
   - AccountManager: Account management

3. **Infrastructure Layer**
   - HTTPClient: Connection pooling
   - Cache: File-based caching
   - Logger: Structured logging
   - RateLimiter: API rate limiting

4. **Platform Layer** (classes)
   - YouTube: Video automation
   - Twitter: Social media automation
   - AffiliateMarketing: Affiliate campaigns
   - Outreach: Outreach automation

Getting Started
---------------

Installation
~~~~~~~~~~~~

.. code-block:: bash

   pip install -r requirements.txt

Configuration
~~~~~~~~~~~~~

1. Copy the example environment file:

.. code-block:: bash

   cp .env.example .env

2. Set your API keys in ``.env``:

.. code-block:: bash

   MISTRAL_API_KEY=your_key_here
   VENICE_API_KEY=your_key_here
   ASSEMBLYAI_API_KEY=your_key_here

3. Configure ``config.json`` with your settings.

See :doc:`../CONFIGURATION` for detailed configuration options.

Usage Example
~~~~~~~~~~~~~

.. code-block:: python

   from classes.YouTube import YouTube
   from logger import setup_logger

   # Set up logging
   logger = setup_logger(__name__)

   # Create YouTube automation instance
   youtube = YouTube(
       account_uuid="your-account-uuid",
       fp_profile_path="/path/to/firefox/profile",
       video_topic="AI Technology"
   )

   # Generate and upload video
   youtube.generate_video()

Development
-----------

Running Tests
~~~~~~~~~~~~~

.. code-block:: bash

   # Run all tests
   make test

   # Run with coverage
   pytest tests/ --cov=src --cov-report=html

Code Quality
~~~~~~~~~~~~

.. code-block:: bash

   # Format code
   make format

   # Run linting
   make lint

   # Type checking
   make type-check

   # All quality checks
   make quality

Project Status
--------------

**Version**: 2.0.0
**Status**: Production-ready
**Technical Debt**: 88.7% resolved (Phase 9 completed)

Recent Improvements:

- ✅ Phase 9: Type hint coverage to ~95%
- ✅ Phase 8: Dependency injection & LLM caching
- ✅ Phase 7: Error handling & performance optimization
- ✅ All critical, high, and medium priority issues resolved

See :doc:`../TECHNICAL_DEBT` for complete cleanup history.

Contributing
------------

When contributing, please:

1. Run ``make quality`` before committing
2. Write tests for new features
3. Follow naming conventions (see :doc:`../NAMING_CONVENTIONS`)
4. Use Google-style docstrings (see :doc:`../DOCSTRING_STYLE_GUIDE`)
5. Use custom exceptions from ``exceptions.py``
6. Apply error handling decorators where appropriate

License
-------

See the LICENSE file in the repository root.

Support
-------

For issues, questions, or contributions, please visit the project repository.
