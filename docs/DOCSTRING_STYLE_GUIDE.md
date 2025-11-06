# Docstring Style Guide

This document defines the standard docstring format for MoneyPrinterV2.

## Standard: Google Style

We use **Google-style docstrings** for all Python code in this project.

### Why Google Style?

- **Readability:** Clean, natural language format
- **Consistency:** Widely adopted standard
- **Tool Support:** Works with Sphinx, PyCharm, VS Code
- **Simple:** Easier to write and maintain than NumPy or reStructuredText

---

## Module-Level Docstrings

Every Python file should start with a module-level docstring:

```python
"""
Brief one-line summary of the module.

Longer description providing context about what this module does,
its purpose, and how it fits into the overall project.
"""

import os
import sys
# ...
```

**Example:**
```python
"""
HTTP Client with connection pooling and retry logic.

This module provides a centralized HTTP client service that:
- Uses requests.Session for connection pooling
- Implements retry logic for transient failures
- Provides a consistent interface for HTTP requests
"""
```

---

## Class Docstrings

Classes should have a docstring that describes their purpose and usage:

```python
class ClassName:
    """
    Brief summary of what this class does.

    Longer description with more details about the class's purpose,
    responsibilities, and important patterns (e.g., singleton, factory).

    Attributes:
        attribute_name: Description of the attribute
        another_attr: Description of another attribute

    Example:
        >>> instance = ClassName(param="value")
        >>> result = instance.method()
    """

    def __init__(self, param: str):
        """
        Initialize the class.

        Args:
            param: Description of the parameter

        Raises:
            ValueError: If param is invalid
        """
        self.attribute_name = param
```

---

## Method/Function Docstrings

### Standard Format

```python
def function_name(param1: str, param2: int = 10) -> str:
    """
    Brief one-line summary of what the function does.

    Longer description providing more details about the function's
    behavior, algorithm, or important notes.

    Args:
        param1: Description of first parameter
        param2: Description of second parameter (default: 10)

    Returns:
        Description of the return value

    Raises:
        ValueError: When param1 is empty
        TypeError: When param2 is not an integer

    Example:
        >>> result = function_name("test", 20)
        >>> print(result)
        'test: 20'

    Note:
        Additional notes about usage, performance, or gotchas.
    """
    if not param1:
        raise ValueError("param1 cannot be empty")
    return f"{param1}: {param2}"
```

### Sections

**Required sections:**
- Brief summary (first line)
- `Args:` (if function takes arguments)
- `Returns:` (if function returns a value)

**Optional sections (use when relevant):**
- Longer description (after brief summary)
- `Raises:` (if function raises exceptions)
- `Example:` (for complex functions or public APIs)
- `Note:` (for important warnings or performance notes)
- `Yields:` (for generators)
- `Attributes:` (for classes)

---

## Examples by Function Type

### Simple Function

```python
def build_url(youtube_video_id: str) -> str:
    """
    Builds the URL to the YouTube video.

    Args:
        youtube_video_id: The YouTube video ID

    Returns:
        The full URL to the YouTube video
    """
    return f"https://www.youtube.com/watch?v={youtube_video_id}"
```

### Function with No Parameters

```python
def get_verbose() -> bool:
    """
    Gets the verbose flag from environment or config file.

    Checks VERBOSE environment variable first,
    then falls back to config.json.

    Returns:
        The verbose flag value
    """
    verbose_env = os.getenv("VERBOSE")
    if verbose_env is not None:
        return verbose_env.lower() in ("true", "1", "yes")
    return _config.get("verbose", False)
```

### Function with Defaults

```python
def validate_integer(
    value: Union[str, int],
    min_value: Optional[int] = None,
    max_value: Optional[int] = None,
    field_name: str = "value",
) -> int:
    """
    Validate and convert a value to integer within specified range.

    Args:
        value: The value to validate (string or int)
        min_value: Minimum allowed value (inclusive)
        max_value: Maximum allowed value (inclusive)
        field_name: Name of the field for error messages (default: "value")

    Returns:
        Validated integer value

    Raises:
        ValueError: If validation fails or value is out of range
    """
    # Implementation...
```

### Context Managers

```python
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

    def __enter__(self) -> webdriver.Firefox:
        """
        Create and return the browser instance.

        Returns:
            Configured Firefox WebDriver instance
        """
        # Implementation...

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Clean up browser instance on context exit.

        Args:
            exc_type: Exception type if an exception was raised
            exc_val: Exception value if an exception was raised
            exc_tb: Exception traceback if an exception was raised

        Returns:
            False to propagate exceptions
        """
        # Implementation...
```

### Property Decorators

```python
@property
def client(self) -> Mistral:
    """
    Get or create the Mistral client instance.

    Lazily initializes the client on first access.

    Returns:
        Mistral client instance
    """
    if self._client is None:
        self._client = Mistral(api_key=self.api_key)
    return self._client
```

### Static Methods

```python
@staticmethod
def create_firefox_browser(
    profile_path: str,
    headless: bool = False
) -> webdriver.Firefox:
    """
    Create a Firefox browser instance with the specified configuration.

    Args:
        profile_path: Path to the Firefox profile directory
        headless: Whether to run browser in headless mode (default: False)

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
    # Implementation...
```

### Class Methods

```python
@classmethod
def get_instance(
    cls,
    api_key: str,
    default_model: str = "mistral-medium-latest"
) -> "LLMService":
    """
    Get or create an LLM service instance for the given API key.

    Uses singleton pattern to reuse client instances for the same API key.

    Args:
        api_key: The API key for the LLM provider
        default_model: Default model to use for completions

    Returns:
        LLMService instance

    Example:
        >>> service = LLMService.get_instance(api_key="sk-...")
    """
    # Implementation...
```

---

## Common Patterns

### Returns None

```python
def close_browser() -> None:
    """
    Closes the browser instance.

    This method ensures all browser windows are closed and resources
    are properly freed.
    """
    # No Returns: section needed for None
```

### Multiple Return Types

```python
def generate_response(self, prompt: str) -> Optional[str]:
    """
    Generates an LLM Response based on a prompt.

    Args:
        prompt: The prompt to use in the text generation

    Returns:
        The generated AI response, or None if generation fails
    """
    # Implementation...
```

### Generator Functions

```python
def process_items(items: List[str]) -> Generator[str, None, None]:
    """
    Process items one by one and yield results.

    Args:
        items: List of items to process

    Yields:
        Processed item string

    Example:
        >>> for result in process_items(["a", "b", "c"]):
        ...     print(result)
    """
    for item in items:
        yield f"Processed: {item}"
```

---

## Don'ts

### ❌ Don't Repeat Type Information

```python
# Bad - type info already in signature
def get_config(key: str) -> str:
    """
    Get config.

    Args:
        key (str): config key (str)

    Returns:
        str: config value (str)
    """
```

```python
# Good
def get_config(key: str) -> str:
    """
    Get configuration value for the given key.

    Args:
        key: Configuration key to retrieve

    Returns:
        Configuration value, or empty string if not found
    """
```

### ❌ Don't Write Useless Docstrings

```python
# Bad
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b
```

```python
# Good (if needed at all for such simple functions)
def add(a: int, b: int) -> int:
    """
    Add two integers and return the sum.

    Args:
        a: First integer
        b: Second integer

    Returns:
        Sum of a and b
    """
    return a + b
```

### ❌ Don't Use Old-Style Formats

```python
# Bad - reStructuredText style
def func(param):
    """
    :param param: description
    :type param: str
    :returns: result
    :rtype: bool
    """
```

```python
# Good - Google style
def func(param: str) -> bool:
    """
    Brief description.

    Args:
        param: Description of parameter

    Returns:
        Description of return value
    """
```

---

## Tools & Validation

### Auto-generation

Use tools to auto-generate docstrings:
- **VS Code:** Python Docstring Generator extension
- **PyCharm:** Built-in docstring generation (Alt+Enter)
- **Command-line:** `pydocstyle` for validation

### Validation

```bash
# Check docstring style compliance
pydocstyle src/

# Type check with docstrings
mypy src/ --check-untyped-defs
```

---

## Summary Checklist

When writing docstrings, ensure:

- [ ] Module has a brief summary at the top
- [ ] Classes have a description and usage example (if complex)
- [ ] All public functions have docstrings
- [ ] Docstrings start with a brief one-line summary
- [ ] Args section lists all parameters
- [ ] Returns section describes return value (if not None)
- [ ] Raises section lists expected exceptions
- [ ] Examples provided for complex or public APIs
- [ ] No type information duplicated from type hints
- [ ] Clear, concise language (no fluff)

---

## References

- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
- [PEP 257 - Docstring Conventions](https://www.python.org/dev/peps/pep-0257/)
- [Sphinx Google Style Guide](https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html)
