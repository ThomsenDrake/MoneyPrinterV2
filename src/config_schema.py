"""
Configuration schema validation using Pydantic.

This module provides data validation and type checking for config.json
to catch configuration errors early and provide clear error messages.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from constants import (
    DEFAULT_HEADLESS,
    DEFAULT_IS_FOR_KIDS,
    DEFAULT_SCRAPER_TIMEOUT,
    DEFAULT_SCRIPT_SENTENCE_LENGTH,
    DEFAULT_THREADS,
    DEFAULT_TWITTER_LANGUAGE,
    DEFAULT_VERBOSE,
    DEFAULT_ZIP_URL,
)


class EmailCredentials(BaseModel):
    """Email credentials configuration."""

    username: str = Field(..., min_length=1, description="Email username")
    password: str = Field(..., min_length=1, description="Email password")

    model_config = ConfigDict(extra="forbid")


class ConfigSchema(BaseModel):
    """
    Main configuration schema for MoneyPrinterV2.

    This schema validates all configuration values and provides type safety.
    Using Pydantic ensures that invalid configurations are caught early
    with clear error messages.
    """

    # General settings
    verbose: bool = Field(default=DEFAULT_VERBOSE, description="Enable verbose logging")
    headless: bool = Field(default=DEFAULT_HEADLESS, description="Run browser in headless mode")

    # Browser configuration
    firefox_profile: str = Field(..., min_length=1, description="Path to Firefox profile")

    # AI/LLM configuration
    llm: Optional[str] = Field(default=None, description="LLM model to use")
    mistral_api_key: str = Field(
        default="", description="Mistral AI API key (should use env var instead)"
    )
    venice_api_key: str = Field(
        default="", description="Venice AI API key (should use env var instead)"
    )
    assembly_ai_api_key: str = Field(
        default="", description="AssemblyAI API key (should use env var instead)"
    )

    # Image generation
    image_model: Optional[str] = Field(default=None, description="Image generation model")
    image_prompt_llm: Optional[str] = Field(
        default=None, description="LLM for image prompt generation"
    )

    # Media settings
    font: Optional[str] = Field(default=None, description="Path to font file for subtitles")
    imagemagick_path: Optional[str] = Field(default=None, description="Path to ImageMagick binary")
    threads: int = Field(
        default=DEFAULT_THREADS, ge=1, le=32, description="Number of threads for processing"
    )

    # Content settings
    script_sentence_length: int = Field(
        default=DEFAULT_SCRIPT_SENTENCE_LENGTH,
        ge=1,
        le=20,
        description="Target sentence length for scripts",
    )

    # Platform-specific
    is_for_kids: bool = Field(
        default=DEFAULT_IS_FOR_KIDS, description="Content is for kids (YouTube)"
    )
    twitter_language: str = Field(
        default=DEFAULT_TWITTER_LANGUAGE, description="Twitter language code"
    )

    # External resources
    zip_url: Optional[str] = Field(
        default=DEFAULT_ZIP_URL,
        description="URL to download songs",
    )
    google_maps_scraper: Optional[str] = Field(
        default=None, description="URL to Google Maps scraper"
    )
    google_maps_scraper_niche: Optional[str] = Field(
        default=None, description="Niche for Google Maps scraper"
    )

    # Scraper settings
    scraper_timeout: int = Field(
        default=DEFAULT_SCRAPER_TIMEOUT,
        ge=30,
        le=3600,
        description="Timeout for scraper operations (seconds)",
    )

    # Outreach settings
    outreach_message_subject: Optional[str] = Field(
        default=None, description="Subject line for outreach emails"
    )
    outreach_message_body_file: Optional[str] = Field(
        default=None, description="Path to outreach email body template"
    )

    # Email credentials
    email: Optional[EmailCredentials] = Field(
        default=None, description="Email credentials for automation"
    )

    model_config = ConfigDict(
        extra="allow",  # Allow extra fields for forward compatibility
        validate_assignment=True,  # Validate on attribute assignment
        str_strip_whitespace=True,  # Strip whitespace from strings
    )

    @field_validator("firefox_profile")
    @classmethod
    def validate_firefox_profile(cls, v: str) -> str:
        """Validate Firefox profile path is not empty."""
        if not v or v.strip() == "":
            raise ValueError("Firefox profile path cannot be empty")
        return v

    @field_validator("twitter_language")
    @classmethod
    def validate_language_code(cls, v: str) -> str:
        """Validate language code format."""
        if len(v) < 2:
            raise ValueError("Language code must be at least 2 characters")
        return v.lower()

    @field_validator("threads")
    @classmethod
    def validate_threads(cls, v: int) -> int:
        """Validate thread count is reasonable."""
        if v < 1:
            raise ValueError("Thread count must be at least 1")
        if v > 32:
            raise ValueError("Thread count should not exceed 32")
        return v

    @field_validator("scraper_timeout")
    @classmethod
    def validate_timeout(cls, v: int) -> int:
        """Validate timeout is within reasonable bounds."""
        if v < 30:
            raise ValueError("Scraper timeout must be at least 30 seconds")
        if v > 3600:
            raise ValueError("Scraper timeout should not exceed 1 hour (3600 seconds)")
        return v


def validate_config(config_data: dict) -> ConfigSchema:
    """
    Validate configuration data against the schema.

    Args:
        config_data: Dictionary containing configuration data

    Returns:
        Validated ConfigSchema instance

    Raises:
        ValidationError: If configuration is invalid

    Example:
        >>> config_data = {"verbose": True, "firefox_profile": "/path/to/profile", ...}
        >>> validated_config = validate_config(config_data)
        >>> print(validated_config.verbose)
        True
    """
    return ConfigSchema(**config_data)


def validate_config_file(file_path: str) -> ConfigSchema:
    """
    Validate configuration from a JSON file.

    Args:
        file_path: Path to config.json file

    Returns:
        Validated ConfigSchema instance

    Raises:
        FileNotFoundError: If config file doesn't exist
        JSONDecodeError: If config file has invalid JSON
        ValidationError: If configuration is invalid

    Example:
        >>> validated_config = validate_config_file("config.json")
        >>> print(validated_config.headless)
        False
    """
    import json

    with open(file_path, "r") as f:
        config_data = json.load(f)

    return validate_config(config_data)
