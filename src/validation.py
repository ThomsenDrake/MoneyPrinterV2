"""
Input validation and sanitization utilities.

This module provides functions to validate and sanitize user inputs
to prevent security issues and ensure data integrity.
"""

import logging
import os
import re
from pathlib import Path
from typing import Optional, Union

logger = logging.getLogger(__name__)


def validate_path(
    path: str,
    must_exist: bool = False,
    must_be_dir: bool = False,
    must_be_file: bool = False,
    create_if_missing: bool = False,
) -> Optional[Path]:
    """
    Validate and sanitize a file system path.

    Args:
        path (str): The path to validate
        must_exist (bool): If True, path must already exist
        must_be_dir (bool): If True, path must be a directory
        must_be_file (bool): If True, path must be a file
        create_if_missing (bool): If True, create directory if it doesn't exist

    Returns:
        Optional[Path]: Validated Path object, or None if validation fails

    Raises:
        ValueError: If path validation fails
    """
    if not path or not isinstance(path, str):
        raise ValueError("Path must be a non-empty string")

    try:
        # Resolve to absolute path
        p = Path(path).expanduser().resolve()

        # Check if path exists when required
        if must_exist and not p.exists():
            raise ValueError(f"Path does not exist: {p}")

        # Create directory if requested
        if create_if_missing and not p.exists():
            p.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {p}")

        # Check path type
        if p.exists():
            if must_be_dir and not p.is_dir():
                raise ValueError(f"Path is not a directory: {p}")
            if must_be_file and not p.is_file():
                raise ValueError(f"Path is not a file: {p}")

        return p

    except (OSError, RuntimeError) as e:
        logger.error(f"Path validation error: {str(e)}")
        raise ValueError(f"Invalid path: {str(e)}")


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
        field_name: Name of the field for error messages

    Returns:
        int: Validated integer value

    Raises:
        ValueError: If validation fails
    """
    try:
        int_value = int(value)

        if min_value is not None and int_value < min_value:
            raise ValueError(f"{field_name} must be at least {min_value}")

        if max_value is not None and int_value > max_value:
            raise ValueError(f"{field_name} must be at most {max_value}")

        return int_value

    except (ValueError, TypeError):
        raise ValueError(f"Invalid {field_name}: must be an integer")


def validate_choice(
    value: str,
    valid_choices: list,
    case_sensitive: bool = False,
    field_name: str = "value",
) -> str:
    """
    Validate that a value is one of the allowed choices.

    Args:
        value: The value to validate
        valid_choices: List of valid choices
        case_sensitive: Whether comparison should be case-sensitive
        field_name: Name of the field for error messages

    Returns:
        str: The validated value

    Raises:
        ValueError: If value is not in valid_choices
    """
    if not value:
        raise ValueError(f"{field_name} cannot be empty")

    # Convert to same case if not case-sensitive
    if not case_sensitive:
        value_lower = value.lower()
        valid_lower = [str(c).lower() for c in valid_choices]

        if value_lower not in valid_lower:
            raise ValueError(
                f"Invalid {field_name}: must be one of {', '.join(map(str, valid_choices))}"
            )
        # Return the original case from valid_choices
        idx = valid_lower.index(value_lower)
        return str(valid_choices[idx])
    else:
        if value not in valid_choices:
            raise ValueError(
                f"Invalid {field_name}: must be one of {', '.join(map(str, valid_choices))}"
            )
        return value


def validate_url(value: str, field_name: str = "URL") -> str:
    """
    Validate that a value is a properly formatted URL.

    Args:
        value: The URL to validate
        field_name: Name of the field for error messages

    Returns:
        str: The validated URL

    Raises:
        ValueError: If URL is invalid
    """
    if not value or not isinstance(value, str):
        raise ValueError(f"{field_name} must be a non-empty string")

    # Basic URL pattern validation
    url_pattern = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain
        r"localhost|"  # localhost
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # or IP
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    if not url_pattern.match(value):
        raise ValueError(f"Invalid {field_name}: must be a valid HTTP(S) URL")

    return value


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize a filename by removing/replacing invalid characters.

    Args:
        filename: The filename to sanitize
        max_length: Maximum allowed length

    Returns:
        str: Sanitized filename

    Raises:
        ValueError: If filename is empty after sanitization
    """
    if not filename or not isinstance(filename, str):
        raise ValueError("Filename must be a non-empty string")

    # Remove path separators and other dangerous characters
    # Keep alphanumeric, spaces, hyphens, underscores, and periods
    sanitized = re.sub(r"[^a-zA-Z0-9\s\-_\.]", "", filename)

    # Replace multiple spaces with single space
    sanitized = re.sub(r"\s+", " ", sanitized).strip()

    # Truncate if too long
    if len(sanitized) > max_length:
        # Preserve extension if present
        name, ext = os.path.splitext(sanitized)
        max_name_len = max_length - len(ext)
        sanitized = name[:max_name_len] + ext

    if not sanitized:
        raise ValueError("Filename is empty after sanitization")

    return sanitized


def validate_non_empty_string(value: str, field_name: str = "value", min_length: int = 1) -> str:
    """
    Validate that a string is not empty and meets minimum length.

    Args:
        value: The string to validate
        field_name: Name of the field for error messages
        min_length: Minimum required length

    Returns:
        str: The validated string (stripped of whitespace)

    Raises:
        ValueError: If string is empty or too short
    """
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")

    # Strip whitespace
    value = value.strip()

    if not value:
        raise ValueError(f"{field_name} cannot be empty")

    if len(value) < min_length:
        raise ValueError(f"{field_name} must be at least {min_length} characters")

    return value
