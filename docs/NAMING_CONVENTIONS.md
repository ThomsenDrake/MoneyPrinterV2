# Naming Conventions - MoneyPrinterV2

**Version:** 1.0
**Last Updated:** 2025-11-07
**Status:** Adopted

---

## Overview

This document establishes naming conventions for the MoneyPrinterV2 codebase to ensure consistency, readability, and maintainability. These conventions align with [PEP 8](https://pep8.org/) and Python community best practices.

---

## Table of Contents

1. [General Principles](#general-principles)
2. [Module and Package Names](#module-and-package-names)
3. [Class Names](#class-names)
4. [Function and Method Names](#function-and-method-names)
5. [Variables](#variables)
6. [Constants](#constants)
7. [File Naming](#file-naming)
8. [Import Conventions](#import-conventions)
9. [Current Codebase Patterns](#current-codebase-patterns)
10. [Future Recommendations](#future-recommendations)

---

## General Principles

1. **Clarity over brevity** - Names should be descriptive and self-documenting
2. **Consistency** - Follow established patterns within the codebase
3. **PEP 8 compliance** - Adhere to Python's official style guide
4. **Avoid abbreviations** - Except for well-known terms (API, HTTP, UUID, etc.)
5. **Meaningful names** - Names should convey purpose and intent

---

## Module and Package Names

### Standard Format
- Use **lowercase** with **underscores** (snake_case)
- Short, descriptive names preferred
- Avoid hyphens and special characters

### Examples

✅ **Good:**
```python
# Module names
config.py
http_client.py
llm_service.py
rate_limiter.py
selenium_service.py
```

❌ **Avoid:**
```python
# Don't use hyphens or camelCase
http-client.py
HttpClient.py
HTTPclient.py
```

### Package Structure
```
src/
├── __init__.py              # Package marker with documentation
├── config.py                # Configuration management
├── constants.py             # Application constants
├── exceptions.py            # Custom exception hierarchy
└── classes/                 # Platform integration classes
    ├── __init__.py
    ├── YouTube.py
    └── Twitter.py
```

**Note:** `src/classes/` could be renamed to `src/platforms/` in a future refactor for better clarity.

---

## Class Names

### Standard Format
- Use **PascalCase** (CapitalizedWords)
- Noun-based names
- Descriptive and specific

### Examples

✅ **Good:**
```python
class ConfigManager:
class HTTPClient:
class SeleniumService:
class LLMService:
class AffiliateMarketing:  # Full name, not abbreviated
```

❌ **Avoid:**
```python
class configManager:     # Should be PascalCase
class Config_Manager:    # No underscores
class CM:               # Too abbreviated
```

### Protocol/Interface Names
```python
class ConfigProtocol(Protocol):
class SeleniumProtocol(Protocol):
class CacheProtocol(Protocol):
```
- Use `Protocol` suffix for protocol interfaces
- Follows typing.Protocol conventions

---

## Function and Method Names

### Standard Format
- Use **lowercase** with **underscores** (snake_case)
- Verb-based names for actions
- Descriptive of what the function does

### Examples

✅ **Good:**
```python
def get_config_value(key: str) -> Any:
def validate_api_key(api_key: str) -> bool:
def generate_video_script(topic: str) -> str:
def setup_logger(name: str) -> logging.Logger:
```

❌ **Avoid:**
```python
def getConfigValue():     # Should be snake_case
def ValidateAPIKey():     # Should be snake_case
def gnrtvid():           # Too abbreviated
```

### Special Method Names
```python
def __init__(self):       # Constructor
def __str__(self):        # String representation
def __repr__(self):       # Official representation
def __enter__(self):      # Context manager entry
def __exit__(self):       # Context manager exit
```

### Private Methods
```python
def _internal_helper():   # Single underscore for internal use
def __private_method():   # Double underscore for name mangling (rare)
```

---

## Variables

### Standard Format
- Use **lowercase** with **underscores** (snake_case)
- Descriptive names
- Avoid single-letter names (except in loops/comprehensions)

### Examples

✅ **Good:**
```python
# Local variables
user_choice = 1
api_key = "sk-..."
config_path = "/path/to/config"
video_count = 10

# Loop variables (acceptable)
for i in range(10):
for idx, item in enumerate(items):
for key, value in data.items():
```

❌ **Avoid:**
```python
userChoice = 1           # Should be snake_case
ak = "sk-..."           # Too abbreviated
x = "/path/to/config"   # Not descriptive
```

### Private Variables
```python
_internal_cache = {}     # Single underscore for internal use
__private_var = "value"  # Double underscore (rarely needed)
```

---

## Constants

### Standard Format
- Use **UPPERCASE** with **underscores**
- Defined in `constants.py` or at module level
- Should be truly constant (not reassigned)

### Examples

✅ **Good:**
```python
# From src/constants.py
DEFAULT_VIDEO_LENGTH = 300
MAX_RETRIES = 3
API_TIMEOUT = 30
DEFAULT_MODEL = "mistral-large-latest"
SUPPORTED_LANGUAGES = ["en", "es", "fr"]
```

❌ **Avoid:**
```python
default_video_length = 300  # Should be UPPERCASE
maxRetries = 3              # Should be UPPERCASE with underscores
MAX_RETRIES_VALUE = 3       # Redundant "VALUE" suffix
```

### Configuration Constants
```python
# Config keys (all caps)
CONFIG_KEY_API_KEY = "mistral_api_key"
CONFIG_KEY_MODEL = "default_model"
```

---

## File Naming

### Python Source Files
- Match the primary class name if file contains a single class
- Use snake_case for modules with multiple classes/functions
- Use descriptive names

### Examples

✅ **Good:**
```
YouTube.py              # Contains YouTube class
Twitter.py              # Contains Twitter class
http_client.py          # Contains HTTPClient class
llm_service.py          # Contains LLMService class
```

✅ **Also Acceptable:**
```
AFM.py                  # Contains AffiliateMarketing (AFM is known abbreviation)
Tts.py                  # Contains TTS class (TTS is well-known)
```

### Test Files
```
test_config.py          # Tests for config module
test_llm_service.py     # Tests for LLM service
conftest.py             # pytest configuration
```

### Documentation Files
```
README.md
TECHNICAL_DEBT.md
CONFIGURATION.md
SECRETS_MANAGEMENT.md
```
- Use UPPERCASE for root-level docs
- Use Sentence_Case for detailed docs in `docs/`

---

## Import Conventions

### Import Order (per PEP 8 and isort)
1. Standard library imports
2. Third-party imports
3. Local application imports

### Example
```python
# 1. Standard library
import logging
import os
from typing import Any, Dict, List, Optional

# 2. Third-party
from selenium import webdriver
from mistralai import Mistral
import pytest

# 3. Local application
from config import get_config_value
from constants import DEFAULT_TIMEOUT
from exceptions import ConfigurationError
from classes.YouTube import YouTube
```

### Import Styles

✅ **Preferred:**
```python
from config import get_config_value, get_api_key
from classes.YouTube import YouTube
from typing import Optional, Dict, Any
```

⚠️ **Use sparingly:**
```python
from config import *        # Only in legacy code, avoid in new code
```

❌ **Avoid:**
```python
import config
config.get_config_value()   # Too verbose
```

---

## Current Codebase Patterns

### Established Patterns

1. **Service Classes:**
   - Pattern: `{Purpose}Service`
   - Examples: `LLMService`, `SeleniumService`, `SchedulerService`

2. **Factory Classes:**
   - Pattern: `{Type}Factory`
   - Example: `BrowserFactory`

3. **Manager Classes:**
   - Pattern: `{Domain}Manager`
   - Examples: `ConfigManager`, `AccountManager`

4. **Error Handlers:**
   - Pattern: Decorator functions in `error_handlers.py`
   - Examples: `@retry_on_failure`, `@safe_return`, `@handle_errors`

5. **Protocol Interfaces:**
   - Pattern: `{Purpose}Protocol`
   - Examples: `ConfigProtocol`, `CacheProtocol`, `SeleniumProtocol`

6. **Custom Exceptions:**
   - Pattern: `{Type}Error` inheriting from `MoneyPrinterError`
   - Examples: `APIError`, `ConfigurationError`, `BrowserError`

### Platform Classes

```python
# Platform integration classes (in src/classes/)
YouTube           # YouTube automation
Twitter           # Twitter automation
AffiliateMarketing  # Affiliate marketing (file: AFM.py)
Outreach          # Outreach automation
TTS               # Text-to-speech (file: Tts.py)
```

**Note on File Names:**
- `AFM.py` contains `AffiliateMarketing` class (AFM is the known abbreviation)
- `Tts.py` contains `TTS` class (TTS is well-known)
- This is acceptable as they're well-established abbreviations in the domain

---

## Future Recommendations

### Potential Improvements

1. **Package Rename:**
   - Consider: `src/classes/` → `src/platforms/`
   - Rationale: "platforms" is more descriptive than "classes"
   - Impact: Would require updating ~6 import statements
   - Priority: Low (cosmetic improvement)

2. **Consistent File Naming:**
   - Option A: Match class names exactly (`AffiliateMarketing.py` instead of `AFM.py`)
   - Option B: Keep current pattern (accepted abbreviations)
   - Current Decision: **Keep Option B** (established patterns, domain knowledge)

3. **Module Organization:**
   - Consider organizing `src/` into subpackages:
     - `src/core/` - Core functionality (config, constants, main)
     - `src/services/` - Service classes (llm_service, selenium_service, etc.)
     - `src/infrastructure/` - Infrastructure (cache, logger, http_client)
     - `src/models/` - Data models and protocols
     - `src/platforms/` - Platform integrations (YouTube, Twitter, etc.)
   - Priority: Low (would require significant refactoring)

4. **Import Style Standardization:**
   - Gradually move away from wildcard imports (`from config import *`)
   - Use explicit imports in new code
   - Refactor legacy code opportunistically

---

## Enforcement

### Automated Tools

1. **Black** - Code formatting
   - Configuration: `pyproject.toml`
   - Run: `make format`

2. **isort** - Import sorting
   - Configuration: `pyproject.toml`
   - Run: `make format`

3. **flake8** - Linting
   - Configuration: `.flake8`
   - Run: `make lint`

4. **mypy** - Type checking
   - Configuration: `pyproject.toml`
   - Run: `make type-check`

### Pre-commit Hooks
```bash
# Run all checks
make quality

# Format and check
make all
```

---

## Examples from Codebase

### Well-Named Modules

```python
# src/http_client.py
class HTTPClient:
    """HTTP client with connection pooling."""

# src/selenium_service.py
class SeleniumService:
    """Selenium browser automation abstraction layer."""

# src/llm_cache.py
class LLMCache:
    """LLM response caching with TTL support."""
```

### Well-Named Functions

```python
# From src/validation.py
def validate_choice(value: str, options: List[str]) -> bool:
def validate_integer(value: str, min_value: int, max_value: int) -> int:
def validate_non_empty_string(value: str, field_name: str) -> str:
def sanitize_filename(filename: str) -> str:

# From src/config.py
def get_config_value(key: str, default: Any = None) -> Any:
def get_api_key(service: str) -> Optional[str]:
def reload_config() -> Dict[str, Any]:
```

### Well-Named Constants

```python
# From src/constants.py
DEFAULT_VIDEO_LENGTH = 300
DEFAULT_IMAGE_WIDTH = 1920
DEFAULT_IMAGE_HEIGHT = 1080
MAX_RETRIES = 3
RETRY_DELAY = 2.0
API_TIMEOUT = 30
```

---

## Quick Reference

| Item | Convention | Example |
|------|-----------|---------|
| **Module** | snake_case | `http_client.py` |
| **Class** | PascalCase | `HTTPClient` |
| **Function** | snake_case | `get_config_value()` |
| **Variable** | snake_case | `api_key` |
| **Constant** | UPPER_SNAKE | `MAX_RETRIES` |
| **Private** | _leading_underscore | `_internal_method()` |
| **Protocol** | PascalCase + Protocol | `ConfigProtocol` |
| **Exception** | PascalCase + Error | `ConfigurationError` |

---

## References

- [PEP 8 - Style Guide for Python Code](https://pep8.org/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Python Naming Conventions](https://visualgit.readthedocs.io/en/latest/pages/naming_convention.html)
- MoneyPrinterV2 `docs/DOCSTRING_STYLE_GUIDE.md`

---

## Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2025-11-07 | 1.0 | Initial naming conventions guide created for Phase 10 |

---

**End of Guide**

For questions or suggestions about naming conventions, please open an issue or discussion in the repository.
