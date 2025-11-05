"""
Unit tests for configuration management (src/config.py).
"""
import os
import json
import pytest
from unittest.mock import patch, mock_open
import tempfile


class TestConfigManager:
    """Tests for the ConfigManager singleton class."""

    def test_singleton_pattern(self):
        """Test that ConfigManager is a singleton."""
        from config import ConfigManager

        instance1 = ConfigManager()
        instance2 = ConfigManager()

        assert instance1 is instance2

    def test_get_with_existing_key(self, mock_config_data):
        """Test getting a configuration value that exists."""
        from config import ConfigManager

        with patch.object(ConfigManager, '_load_config') as mock_load:
            ConfigManager._config = mock_config_data
            manager = ConfigManager()

            result = manager.get("verbose")
            assert result is True

    def test_get_with_missing_key_returns_default(self, mock_config_data):
        """Test getting a configuration value with a missing key returns default."""
        from config import ConfigManager

        with patch.object(ConfigManager, '_load_config') as mock_load:
            ConfigManager._config = mock_config_data
            manager = ConfigManager()

            result = manager.get("nonexistent_key", "default_value")
            assert result == "default_value"

    def test_get_nested_value(self, mock_config_data):
        """Test getting a nested configuration value."""
        from config import ConfigManager

        with patch.object(ConfigManager, '_load_config') as mock_load:
            ConfigManager._config = mock_config_data
            manager = ConfigManager()

            result = manager.get("email")
            assert result == {"username": "test@example.com", "password": "test-password"}

    def test_load_config_file_not_found(self, temp_dir):
        """Test loading configuration when file doesn't exist."""
        from config import ConfigManager

        # Reset singleton
        ConfigManager._instance = None
        ConfigManager._config = None

        with patch.object(ConfigManager, '_config_path', str(temp_dir / "nonexistent.json")):
            ConfigManager._load_config()
            assert ConfigManager._config == {}

    def test_load_config_invalid_json(self, temp_dir):
        """Test loading configuration with invalid JSON."""
        from config import ConfigManager

        # Create invalid JSON file
        invalid_json_file = temp_dir / "invalid.json"
        with open(invalid_json_file, 'w') as f:
            f.write("{invalid json content")

        ConfigManager._instance = None
        ConfigManager._config = None
        ConfigManager._config_path = str(invalid_json_file)

        ConfigManager._load_config()
        assert ConfigManager._config == {}

    def test_reload_config(self, mock_config_file):
        """Test reloading configuration from disk."""
        from config import ConfigManager

        # Set initial config
        ConfigManager._instance = None
        ConfigManager._config = None
        ConfigManager._config_path = str(mock_config_file)

        ConfigManager._load_config()
        initial_verbose = ConfigManager._config.get("verbose")

        # Modify the config file
        with open(mock_config_file, 'r') as f:
            config_data = json.load(f)
        config_data["verbose"] = not initial_verbose
        with open(mock_config_file, 'w') as f:
            json.dump(config_data, f)

        # Reload and check
        ConfigManager.reload()
        assert ConfigManager._config.get("verbose") == (not initial_verbose)


class TestConfigGetters:
    """Tests for configuration getter functions."""

    @pytest.fixture(autouse=True)
    def setup_config(self, mock_config_data):
        """Setup configuration before each test."""
        from config import ConfigManager

        ConfigManager._instance = None
        ConfigManager._config = mock_config_data

    def test_get_verbose(self):
        """Test get_verbose returns correct value."""
        from config import get_verbose

        result = get_verbose()
        assert result is True

    def test_get_verbose_default(self):
        """Test get_verbose returns False when not set."""
        from config import ConfigManager, get_verbose

        ConfigManager._config = {}
        result = get_verbose()
        assert result is False

    def test_get_firefox_profile_path(self):
        """Test get_firefox_profile_path returns correct value."""
        from config import get_firefox_profile_path

        result = get_firefox_profile_path()
        assert result == "/path/to/firefox/profile"

    def test_get_headless(self):
        """Test get_headless returns correct value."""
        from config import get_headless

        result = get_headless()
        assert result is False

    def test_get_email_credentials(self):
        """Test get_email_credentials returns correct dict."""
        from config import get_email_credentials

        result = get_email_credentials()
        assert result == {"username": "test@example.com", "password": "test-password"}

    def test_get_email_credentials_default(self):
        """Test get_email_credentials returns empty dict when not set."""
        from config import ConfigManager, get_email_credentials

        ConfigManager._config = {}
        result = get_email_credentials()
        assert result == {}

    def test_get_threads_default(self):
        """Test get_threads returns default value when not set."""
        from config import ConfigManager, get_threads

        ConfigManager._config = {}
        result = get_threads()
        assert result == 1

    def test_get_scraper_timeout_default(self):
        """Test get_scraper_timeout returns default value."""
        from config import get_scraper_timeout

        result = get_scraper_timeout()
        assert result == 300

    def test_get_is_for_kids_default(self):
        """Test get_is_for_kids returns default False."""
        from config import ConfigManager, get_is_for_kids

        ConfigManager._config = {}
        result = get_is_for_kids()
        assert result is False

    def test_get_mistral_api_key(self):
        """Test get_mistral_api_key returns correct value."""
        from config import get_mistral_api_key

        result = get_mistral_api_key()
        assert result == "test-mistral-key"

    def test_get_venice_api_key(self):
        """Test get_venice_api_key returns correct value."""
        from config import get_venice_api_key

        result = get_venice_api_key()
        assert result == "test-venice-key"

    def test_get_assemblyai_api_key(self):
        """Test get_assemblyai_api_key returns correct value."""
        from config import get_assemblyai_api_key

        result = get_assemblyai_api_key()
        assert result == "test-assemblyai-key"

    def test_get_twitter_language_default(self):
        """Test get_twitter_language returns default 'en'."""
        from config import ConfigManager, get_twitter_language

        ConfigManager._config = {}
        result = get_twitter_language()
        assert result == "en"

    def test_get_script_sentence_length_default(self):
        """Test get_script_sentence_length returns default 4."""
        from config import ConfigManager, get_script_sentence_length

        ConfigManager._config = {}
        result = get_script_sentence_length()
        assert result == 4


class TestFolderStructure:
    """Tests for folder structure management."""

    def test_get_first_time_running_true(self, temp_dir):
        """Test detecting first time running when .mp folder doesn't exist."""
        from config import get_first_time_running

        with patch('config.ROOT_DIR', str(temp_dir)):
            result = get_first_time_running()
            assert result is True

    def test_get_first_time_running_false(self, temp_dir):
        """Test detecting not first time when .mp folder exists."""
        from config import get_first_time_running

        # Create .mp folder
        mp_dir = temp_dir / ".mp"
        mp_dir.mkdir()

        with patch('config.ROOT_DIR', str(temp_dir)):
            result = get_first_time_running()
            assert result is False

    def test_assert_folder_structure_creates_mp_folder(self, temp_dir):
        """Test that assert_folder_structure creates .mp folder."""
        from config import assert_folder_structure

        with patch('config.ROOT_DIR', str(temp_dir)):
            with patch('config.get_verbose', return_value=False):
                assert_folder_structure()

            mp_dir = temp_dir / ".mp"
            assert mp_dir.exists()
            assert mp_dir.is_dir()

    def test_assert_folder_structure_no_duplicate_creation(self, temp_dir):
        """Test that assert_folder_structure doesn't fail if folder exists."""
        from config import assert_folder_structure

        # Create .mp folder first
        mp_dir = temp_dir / ".mp"
        mp_dir.mkdir()

        with patch('config.ROOT_DIR', str(temp_dir)):
            with patch('config.get_verbose', return_value=False):
                # Should not raise exception
                assert_folder_structure()

            assert mp_dir.exists()


class TestEqualizeSubtitles:
    """Tests for subtitle equalization function."""

    def test_equalize_subtitles_calls_srt_equalizer(self, temp_dir):
        """Test that equalize_subtitles calls srt_equalizer correctly."""
        from config import equalize_subtitles
        import srt_equalizer

        srt_file = temp_dir / "test.srt"
        srt_file.write_text("1\n00:00:00,000 --> 00:00:02,000\nTest subtitle\n")

        with patch.object(srt_equalizer, 'equalize_srt_file') as mock_equalize:
            equalize_subtitles(str(srt_file), max_chars=15)

            mock_equalize.assert_called_once_with(str(srt_file), str(srt_file), 15)

    def test_equalize_subtitles_default_max_chars(self, temp_dir):
        """Test equalize_subtitles uses default max_chars."""
        from config import equalize_subtitles
        import srt_equalizer

        srt_file = temp_dir / "test.srt"
        srt_file.write_text("1\n00:00:00,000 --> 00:00:02,000\nTest\n")

        with patch.object(srt_equalizer, 'equalize_srt_file') as mock_equalize:
            equalize_subtitles(str(srt_file))

            mock_equalize.assert_called_once_with(str(srt_file), str(srt_file), 10)
