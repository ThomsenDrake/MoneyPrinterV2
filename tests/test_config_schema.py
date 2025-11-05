"""
Unit tests for configuration schema validation (src/config_schema.py).
"""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError


class TestEmailCredentials:
    """Tests for EmailCredentials schema."""

    def test_valid_email_credentials(self):
        """Test creating valid email credentials."""
        from config_schema import EmailCredentials

        creds = EmailCredentials(username="test@example.com", password="secure_password")

        assert creds.username == "test@example.com"
        assert creds.password == "secure_password"

    def test_email_credentials_empty_username(self):
        """Test that empty username is rejected."""
        from config_schema import EmailCredentials

        with pytest.raises(ValidationError):
            EmailCredentials(username="", password="password")

    def test_email_credentials_empty_password(self):
        """Test that empty password is rejected."""
        from config_schema import EmailCredentials

        with pytest.raises(ValidationError):
            EmailCredentials(username="user@test.com", password="")

    def test_email_credentials_missing_fields(self):
        """Test that missing required fields are rejected."""
        from config_schema import EmailCredentials

        with pytest.raises(ValidationError):
            EmailCredentials(username="user@test.com")


class TestConfigSchema:
    """Tests for ConfigSchema validation."""

    def test_minimal_valid_config(self):
        """Test creating config with minimal required fields."""
        from config_schema import ConfigSchema

        config = ConfigSchema(firefox_profile="/path/to/profile")

        assert config.firefox_profile == "/path/to/profile"
        assert config.verbose is False
        assert config.headless is False
        assert config.threads == 1

    def test_full_valid_config(self):
        """Test creating config with all fields."""
        from config_schema import ConfigSchema, EmailCredentials

        config_data = {
            "verbose": True,
            "headless": False,
            "firefox_profile": "/path/to/profile",
            "llm": "mistral-large-latest",
            "mistral_api_key": "test-key",
            "venice_api_key": "test-key",
            "assembly_ai_api_key": "test-key",
            "image_model": "flux-pro",
            "image_prompt_llm": "mistral",
            "font": "/path/to/font.ttf",
            "imagemagick_path": "/usr/bin/convert",
            "threads": 4,
            "script_sentence_length": 5,
            "is_for_kids": False,
            "twitter_language": "en",
            "scraper_timeout": 300,
            "email": {"username": "test@example.com", "password": "password"},
        }

        config = ConfigSchema(**config_data)

        assert config.verbose is True
        assert config.threads == 4
        assert config.script_sentence_length == 5
        assert config.email.username == "test@example.com"

    def test_empty_firefox_profile_rejected(self):
        """Test that empty Firefox profile is rejected."""
        from config_schema import ConfigSchema

        with pytest.raises(ValidationError, match="Firefox profile path cannot be empty"):
            ConfigSchema(firefox_profile="")

    def test_whitespace_firefox_profile_rejected(self):
        """Test that whitespace-only Firefox profile is rejected."""
        from config_schema import ConfigSchema

        with pytest.raises(ValidationError):
            ConfigSchema(firefox_profile="   ")

    def test_invalid_thread_count_too_low(self):
        """Test that thread count less than 1 is rejected."""
        from config_schema import ConfigSchema

        with pytest.raises(ValidationError, match="Thread count must be at least 1"):
            ConfigSchema(firefox_profile="/path", threads=0)

    def test_invalid_thread_count_too_high(self):
        """Test that thread count greater than 32 is rejected."""
        from config_schema import ConfigSchema

        with pytest.raises(ValidationError):
            ConfigSchema(firefox_profile="/path", threads=100)

    def test_invalid_scraper_timeout_too_low(self):
        """Test that scraper timeout less than 30 is rejected."""
        from config_schema import ConfigSchema

        with pytest.raises(ValidationError, match="at least 30 seconds"):
            ConfigSchema(firefox_profile="/path", scraper_timeout=10)

    def test_invalid_scraper_timeout_too_high(self):
        """Test that scraper timeout greater than 3600 is rejected."""
        from config_schema import ConfigSchema

        with pytest.raises(ValidationError, match="should not exceed 1 hour"):
            ConfigSchema(firefox_profile="/path", scraper_timeout=5000)

    def test_twitter_language_validation(self):
        """Test Twitter language code validation."""
        from config_schema import ConfigSchema

        # Valid language code
        config = ConfigSchema(firefox_profile="/path", twitter_language="EN")
        assert config.twitter_language == "en"  # Should be lowercased

        # Invalid language code (too short)
        with pytest.raises(ValidationError, match="at least 2 characters"):
            ConfigSchema(firefox_profile="/path", twitter_language="e")

    def test_default_values(self):
        """Test that default values are set correctly."""
        from config_schema import ConfigSchema

        config = ConfigSchema(firefox_profile="/path/to/profile")

        assert config.verbose is False
        assert config.headless is False
        assert config.threads == 1
        assert config.script_sentence_length == 4
        assert config.is_for_kids is False
        assert config.twitter_language == "en"
        assert config.scraper_timeout == 300

    def test_extra_fields_allowed(self):
        """Test that extra fields are allowed for forward compatibility."""
        from config_schema import ConfigSchema

        config_data = {
            "firefox_profile": "/path",
            "future_field": "some_value",
            "another_new_field": 123,
        }

        config = ConfigSchema(**config_data)
        assert config.firefox_profile == "/path"

    def test_whitespace_stripping(self):
        """Test that whitespace is stripped from string fields."""
        from config_schema import ConfigSchema

        config = ConfigSchema(firefox_profile="  /path/to/profile  ")
        assert config.firefox_profile == "/path/to/profile"

    def test_nested_email_validation(self):
        """Test nested email credentials validation."""
        from config_schema import ConfigSchema

        # Valid nested email
        config = ConfigSchema(
            firefox_profile="/path", email={"username": "user@test.com", "password": "pass"}
        )
        assert config.email.username == "user@test.com"

        # Invalid nested email
        with pytest.raises(ValidationError):
            ConfigSchema(firefox_profile="/path", email={"username": "", "password": "pass"})


class TestValidateConfigFunction:
    """Tests for validate_config helper function."""

    def test_validate_config_valid_data(self):
        """Test validating valid configuration data."""
        from config_schema import validate_config

        config_data = {"firefox_profile": "/path/to/profile", "verbose": True, "threads": 4}

        config = validate_config(config_data)

        assert config.firefox_profile == "/path/to/profile"
        assert config.verbose is True
        assert config.threads == 4

    def test_validate_config_invalid_data(self):
        """Test validating invalid configuration data."""
        from config_schema import validate_config

        config_data = {"firefox_profile": "", "threads": -1}  # Invalid  # Invalid

        with pytest.raises(ValidationError):
            validate_config(config_data)

    def test_validate_config_missing_required_field(self):
        """Test validating config with missing required field."""
        from config_schema import validate_config

        config_data = {
            "verbose": True
            # Missing firefox_profile
        }

        with pytest.raises(ValidationError):
            validate_config(config_data)


class TestValidateConfigFile:
    """Tests for validate_config_file function."""

    def test_validate_config_file_success(self, temp_dir):
        """Test validating a valid config file."""
        from config_schema import validate_config_file

        config_file = temp_dir / "config.json"
        config_data = {"firefox_profile": "/path/to/profile", "verbose": True, "threads": 2}

        with open(config_file, "w") as f:
            json.dump(config_data, f)

        config = validate_config_file(str(config_file))

        assert config.firefox_profile == "/path/to/profile"
        assert config.verbose is True
        assert config.threads == 2

    def test_validate_config_file_invalid_json(self, temp_dir):
        """Test validating file with invalid JSON."""
        from config_schema import validate_config_file

        config_file = temp_dir / "invalid.json"
        config_file.write_text("{invalid json")

        with pytest.raises(json.JSONDecodeError):
            validate_config_file(str(config_file))

    def test_validate_config_file_invalid_schema(self, temp_dir):
        """Test validating file with invalid schema."""
        from config_schema import validate_config_file

        config_file = temp_dir / "config.json"
        config_data = {"firefox_profile": "", "threads": 100}  # Invalid  # Invalid

        with open(config_file, "w") as f:
            json.dump(config_data, f)

        with pytest.raises(ValidationError):
            validate_config_file(str(config_file))

    def test_validate_config_file_not_found(self):
        """Test validating non-existent file."""
        from config_schema import validate_config_file

        with pytest.raises(FileNotFoundError):
            validate_config_file("/nonexistent/config.json")


class TestBoundaryValues:
    """Tests for boundary values in validation."""

    def test_threads_boundary_values(self):
        """Test thread count boundary values."""
        from config_schema import ConfigSchema

        # Minimum valid
        config = ConfigSchema(firefox_profile="/path", threads=1)
        assert config.threads == 1

        # Maximum valid
        config = ConfigSchema(firefox_profile="/path", threads=32)
        assert config.threads == 32

        # Just below minimum (invalid)
        with pytest.raises(ValidationError):
            ConfigSchema(firefox_profile="/path", threads=0)

        # Just above maximum (invalid)
        with pytest.raises(ValidationError):
            ConfigSchema(firefox_profile="/path", threads=33)

    def test_scraper_timeout_boundary_values(self):
        """Test scraper timeout boundary values."""
        from config_schema import ConfigSchema

        # Minimum valid
        config = ConfigSchema(firefox_profile="/path", scraper_timeout=30)
        assert config.scraper_timeout == 30

        # Maximum valid
        config = ConfigSchema(firefox_profile="/path", scraper_timeout=3600)
        assert config.scraper_timeout == 3600

        # Just below minimum (invalid)
        with pytest.raises(ValidationError):
            ConfigSchema(firefox_profile="/path", scraper_timeout=29)

        # Just above maximum (invalid)
        with pytest.raises(ValidationError):
            ConfigSchema(firefox_profile="/path", scraper_timeout=3601)

    def test_script_sentence_length_boundaries(self):
        """Test script sentence length boundary values."""
        from config_schema import ConfigSchema

        # Minimum valid
        config = ConfigSchema(firefox_profile="/path", script_sentence_length=1)
        assert config.script_sentence_length == 1

        # Maximum valid
        config = ConfigSchema(firefox_profile="/path", script_sentence_length=20)
        assert config.script_sentence_length == 20

        # Below minimum (invalid)
        with pytest.raises(ValidationError):
            ConfigSchema(firefox_profile="/path", script_sentence_length=0)

        # Above maximum (invalid)
        with pytest.raises(ValidationError):
            ConfigSchema(firefox_profile="/path", script_sentence_length=21)
