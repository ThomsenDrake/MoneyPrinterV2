"""
Unit tests for the setup wizard module (src/setup_wizard.py).
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


class TestFileExists:
    """Tests for the _file_exists helper."""

    def test_file_exists_returns_true_for_existing_file(self, temp_dir):
        """Test that _file_exists returns True when file exists."""
        from setup_wizard import _file_exists

        # Create a test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("test")

        with patch("setup_wizard.ROOT_DIR", str(temp_dir)):
            assert _file_exists("test.txt") is True

    def test_file_exists_returns_false_for_missing_file(self, temp_dir):
        """Test that _file_exists returns False when file is missing."""
        from setup_wizard import _file_exists

        with patch("setup_wizard.ROOT_DIR", str(temp_dir)):
            assert _file_exists("nonexistent.txt") is False


class TestCopyExampleFile:
    """Tests for the _copy_example_file helper."""

    def test_copy_example_file_success(self, temp_dir):
        """Test that example file is copied successfully."""
        from setup_wizard import _copy_example_file

        # Create source file
        source = temp_dir / "example.txt"
        source.write_text("example content")

        with patch("setup_wizard.ROOT_DIR", str(temp_dir)):
            result = _copy_example_file("target.txt", "example.txt")

        assert result is True
        assert (temp_dir / "target.txt").exists()
        assert (temp_dir / "target.txt").read_text() == "example content"

    def test_copy_example_file_source_missing(self, temp_dir):
        """Test that copy fails gracefully when source is missing."""
        from setup_wizard import _copy_example_file

        with patch("setup_wizard.ROOT_DIR", str(temp_dir)):
            result = _copy_example_file("target.txt", "missing.txt")

        assert result is False
        assert not (temp_dir / "target.txt").exists()


class TestCheckEnvKey:
    """Tests for the _check_env_key helper."""

    def test_check_env_key_returns_true_when_set(self):
        """Test that _check_env_key returns True for set variables."""
        from setup_wizard import _check_env_key

        with patch.dict(os.environ, {"TEST_KEY": "some_value"}):
            assert _check_env_key("TEST_KEY") is True

    def test_check_env_key_returns_false_when_empty(self):
        """Test that _check_env_key returns False for empty variables."""
        from setup_wizard import _check_env_key

        with patch.dict(os.environ, {"TEST_KEY": ""}):
            assert _check_env_key("TEST_KEY") is False

    def test_check_env_key_returns_false_when_whitespace(self):
        """Test that _check_env_key returns False for whitespace-only variables."""
        from setup_wizard import _check_env_key

        with patch.dict(os.environ, {"TEST_KEY": "   "}):
            assert _check_env_key("TEST_KEY") is False

    def test_check_env_key_returns_false_when_missing(self):
        """Test that _check_env_key returns False for missing variables."""
        from setup_wizard import _check_env_key

        with patch.dict(os.environ, {}, clear=True):
            assert _check_env_key("NONEXISTENT_KEY") is False


class TestCheckConfigFiles:
    """Tests for the check_config_files function."""

    def test_all_files_present(self, temp_dir):
        """Test when all config files exist."""
        from setup_wizard import check_config_files

        (temp_dir / ".env").write_text("KEY=value")
        (temp_dir / "config.json").write_text("{}")

        with patch("setup_wizard.ROOT_DIR", str(temp_dir)):
            present, missing = check_config_files()

        assert ".env" in present
        assert "config.json" in present
        assert len(missing) == 0

    def test_all_files_missing(self, temp_dir):
        """Test when all config files are missing."""
        from setup_wizard import check_config_files

        with patch("setup_wizard.ROOT_DIR", str(temp_dir)):
            present, missing = check_config_files()

        assert len(present) == 0
        assert ".env" in missing
        assert "config.json" in missing

    def test_partial_files_present(self, temp_dir):
        """Test when only some config files exist."""
        from setup_wizard import check_config_files

        (temp_dir / "config.json").write_text("{}")

        with patch("setup_wizard.ROOT_DIR", str(temp_dir)):
            present, missing = check_config_files()

        assert "config.json" in present
        assert ".env" in missing


class TestCheckApiKeys:
    """Tests for the check_api_keys function."""

    def test_all_keys_configured(self):
        """Test when all API keys are set."""
        from setup_wizard import check_api_keys

        env = {
            "MISTRAL_API_KEY": "test-key",
            "VENICE_API_KEY": "test-key",
            "ASSEMBLYAI_API_KEY": "test-key",
        }
        with patch.dict(os.environ, env, clear=True):
            configured, missing_required, missing_optional = check_api_keys()

        assert "MISTRAL_API_KEY" in configured
        assert len(missing_required) == 0
        assert len(missing_optional) == 0

    def test_missing_required_key(self):
        """Test when required API key is missing."""
        from setup_wizard import check_api_keys

        with patch.dict(os.environ, {}, clear=True):
            configured, missing_required, missing_optional = check_api_keys()

        assert "MISTRAL_API_KEY" in missing_required

    def test_missing_optional_keys(self):
        """Test when optional API keys are missing but required ones are set."""
        from setup_wizard import check_api_keys

        env = {"MISTRAL_API_KEY": "test-key"}
        with patch.dict(os.environ, env, clear=True):
            configured, missing_required, missing_optional = check_api_keys()

        assert "MISTRAL_API_KEY" in configured
        assert len(missing_required) == 0
        assert "VENICE_API_KEY" in missing_optional
        assert "ASSEMBLYAI_API_KEY" in missing_optional


class TestRunStartupChecks:
    """Tests for the run_startup_checks function."""

    def test_startup_checks_pass_with_valid_config(self, temp_dir):
        """Test startup checks pass when everything is configured."""
        from setup_wizard import run_startup_checks

        (temp_dir / ".env").write_text("MISTRAL_API_KEY=test-key")
        (temp_dir / "config.json").write_text("{}")

        env = {"MISTRAL_API_KEY": "test-key"}
        with patch("setup_wizard.ROOT_DIR", str(temp_dir)), patch.dict(os.environ, env, clear=True):
            result = run_startup_checks()

        assert result is True

    def test_startup_checks_warn_missing_env(self, temp_dir):
        """Test startup checks warn when .env is missing."""
        from setup_wizard import run_startup_checks

        (temp_dir / "config.json").write_text("{}")

        env = {"MISTRAL_API_KEY": "test-key"}
        with patch("setup_wizard.ROOT_DIR", str(temp_dir)), patch.dict(os.environ, env, clear=True):
            result = run_startup_checks()

        assert result is False

    def test_startup_checks_warn_missing_api_key(self, temp_dir):
        """Test startup checks warn when API key is missing."""
        from setup_wizard import run_startup_checks

        (temp_dir / ".env").write_text("")
        (temp_dir / "config.json").write_text("{}")

        with patch("setup_wizard.ROOT_DIR", str(temp_dir)), patch.dict(os.environ, {}, clear=True):
            result = run_startup_checks()

        assert result is False


class TestRunSetupWizard:
    """Tests for the run_setup_wizard function."""

    def test_setup_wizard_succeeds_with_all_config(self, temp_dir):
        """Test that wizard reports success when everything is configured."""
        from setup_wizard import run_setup_wizard

        (temp_dir / ".env").write_text("MISTRAL_API_KEY=test-key")
        (temp_dir / "config.json").write_text("{}")

        env = {"MISTRAL_API_KEY": "test-key"}
        with patch("setup_wizard.ROOT_DIR", str(temp_dir)), patch.dict(os.environ, env, clear=True):
            result = run_setup_wizard()

        assert result is True

    def test_setup_wizard_fails_without_required_key(self, temp_dir):
        """Test that wizard reports failure when required key is missing."""
        from setup_wizard import run_setup_wizard

        (temp_dir / ".env").write_text("")
        (temp_dir / "config.json").write_text("{}")

        with patch("setup_wizard.ROOT_DIR", str(temp_dir)), patch.dict(os.environ, {}, clear=True):
            result = run_setup_wizard()

        assert result is False

    def test_setup_wizard_copies_missing_files(self, temp_dir):
        """Test that wizard copies example files when user agrees."""
        from setup_wizard import run_setup_wizard

        # Create example files
        (temp_dir / ".env.example").write_text("# Example env")
        (temp_dir / "config.example.json").write_text('{"verbose": true}')

        env = {"MISTRAL_API_KEY": "test-key"}
        with (
            patch("setup_wizard.ROOT_DIR", str(temp_dir)),
            patch.dict(os.environ, env, clear=True),
            patch("builtins.input", return_value="yes"),
        ):
            result = run_setup_wizard()

        assert (temp_dir / ".env").exists()
        assert (temp_dir / "config.json").exists()

    def test_setup_wizard_skips_copy_when_declined(self, temp_dir):
        """Test that wizard skips copy when user declines."""
        from setup_wizard import run_setup_wizard

        (temp_dir / ".env.example").write_text("# Example env")
        (temp_dir / "config.example.json").write_text('{"verbose": true}')

        with (
            patch("setup_wizard.ROOT_DIR", str(temp_dir)),
            patch.dict(os.environ, {}, clear=True),
            patch("builtins.input", return_value="no"),
        ):
            result = run_setup_wizard()

        assert not (temp_dir / ".env").exists()
        assert not (temp_dir / "config.json").exists()
        assert result is False
