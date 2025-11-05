"""
Unit tests for utility functions (src/utils.py).
"""
import os
import pytest
import platform
import zipfile
from unittest.mock import patch, MagicMock, mock_open, call
from pathlib import Path


class TestCloseSeleniumInstances:
    """Tests for close_running_selenium_instances function."""

    @pytest.mark.skipif(platform.system() != "Windows", reason="Windows-specific test")
    def test_close_selenium_windows(self):
        """Test closing Selenium instances on Windows."""
        from utils import close_running_selenium_instances

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            close_running_selenium_instances()

            mock_run.assert_called_once_with(
                ["taskkill", "/f", "/im", "firefox.exe"],
                check=False,
                capture_output=True
            )

    @pytest.mark.skipif(platform.system() == "Windows", reason="Unix-specific test")
    def test_close_selenium_unix(self):
        """Test closing Selenium instances on Unix."""
        from utils import close_running_selenium_instances

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            close_running_selenium_instances()

            mock_run.assert_called_once_with(
                ["pkill", "firefox"],
                check=False,
                capture_output=True
            )

    def test_close_selenium_subprocess_error(self):
        """Test handling subprocess error when closing Selenium."""
        from utils import close_running_selenium_instances
        import subprocess

        with patch('subprocess.run', side_effect=subprocess.SubprocessError("Process error")):
            # Should not raise exception, just log error
            close_running_selenium_instances()

    def test_close_selenium_general_exception(self):
        """Test handling general exception when closing Selenium."""
        from utils import close_running_selenium_instances

        with patch('subprocess.run', side_effect=Exception("Unexpected error")):
            # Should not raise exception, just log error
            close_running_selenium_instances()


class TestBuildUrl:
    """Tests for build_url function."""

    def test_build_url_valid_id(self):
        """Test building URL with valid YouTube video ID."""
        from utils import build_url

        video_id = "dQw4w9WgXcQ"
        result = build_url(video_id)

        assert result == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    def test_build_url_different_ids(self):
        """Test building URLs with different video IDs."""
        from utils import build_url

        test_cases = [
            ("abc123", "https://www.youtube.com/watch?v=abc123"),
            ("XyZ-789", "https://www.youtube.com/watch?v=XyZ-789"),
            ("test_video", "https://www.youtube.com/watch?v=test_video"),
        ]

        for video_id, expected_url in test_cases:
            result = build_url(video_id)
            assert result == expected_url


class TestRemTempFiles:
    """Tests for rem_temp_files function."""

    def test_rem_temp_files(self, temp_dir):
        """Test removing temporary files while keeping JSON files."""
        from utils import rem_temp_files
        import config

        # Setup .mp directory with various files
        mp_dir = temp_dir / ".mp"
        mp_dir.mkdir()

        # Create test files
        (mp_dir / "cache.json").write_text("{}")
        (mp_dir / "data.json").write_text("{}")
        (mp_dir / "temp1.txt").write_text("temp")
        (mp_dir / "temp2.mp4").write_text("video")
        (mp_dir / "image.png").write_text("image")

        with patch.object(config, 'ROOT_DIR', str(temp_dir)):
            rem_temp_files()

        # Check that JSON files remain
        assert (mp_dir / "cache.json").exists()
        assert (mp_dir / "data.json").exists()

        # Check that non-JSON files are removed
        assert not (mp_dir / "temp1.txt").exists()
        assert not (mp_dir / "temp2.mp4").exists()
        assert not (mp_dir / "image.png").exists()

    def test_rem_temp_files_empty_directory(self, temp_dir):
        """Test removing temp files from empty directory."""
        from utils import rem_temp_files
        import config

        mp_dir = temp_dir / ".mp"
        mp_dir.mkdir()

        with patch.object(config, 'ROOT_DIR', str(temp_dir)):
            # Should not raise exception
            rem_temp_files()


class TestFetchSongs:
    """Tests for fetch_songs function."""

    def test_fetch_songs_directory_exists(self, temp_dir):
        """Test that fetch_songs skips download if directory exists."""
        from utils import fetch_songs
        import config

        # Create Songs directory
        songs_dir = temp_dir / "Songs"
        songs_dir.mkdir()

        with patch.object(config, 'ROOT_DIR', str(temp_dir)):
            with patch('requests.get') as mock_get:
                fetch_songs()

                # Should not make request if directory exists
                mock_get.assert_not_called()

    def test_fetch_songs_downloads_and_extracts(self, temp_dir):
        """Test that fetch_songs downloads and extracts songs."""
        from utils import fetch_songs
        import config

        # Mock response
        mock_response = MagicMock()
        mock_response.content = b"fake zip content"

        with patch.object(config, 'ROOT_DIR', str(temp_dir)):
            with patch('requests.get', return_value=mock_response):
                with patch('zipfile.ZipFile') as mock_zipfile:
                    mock_zip = MagicMock()
                    mock_zipfile.return_value.__enter__.return_value = mock_zip

                    # Create a real temp zip file for the test
                    songs_dir = temp_dir / "Songs"

                    with patch('builtins.open', mock_open()) as mock_file:
                        with patch('os.remove'):
                            fetch_songs()

                    # Verify directory was created
                    assert songs_dir.exists()

    def test_fetch_songs_network_error(self, temp_dir):
        """Test handling network error when fetching songs."""
        from utils import fetch_songs
        import config
        import requests

        with patch.object(config, 'ROOT_DIR', str(temp_dir)):
            with patch('requests.get', side_effect=requests.RequestException("Network error")):
                # Should not raise exception, just log error
                fetch_songs()

    def test_fetch_songs_bad_zip(self, temp_dir):
        """Test handling bad zip file when fetching songs."""
        from utils import fetch_songs
        import config

        mock_response = MagicMock()
        mock_response.content = b"not a real zip"

        with patch.object(config, 'ROOT_DIR', str(temp_dir)):
            with patch('requests.get', return_value=mock_response):
                with patch('zipfile.ZipFile', side_effect=zipfile.BadZipFile("Bad zip")):
                    with patch('builtins.open', mock_open()):
                        # Should not raise exception
                        fetch_songs()


class TestChooseRandomSong:
    """Tests for choose_random_song function."""

    def test_choose_random_song_success(self, temp_dir):
        """Test choosing a random song successfully."""
        from utils import choose_random_song
        import config

        # Setup Songs directory with files
        songs_dir = temp_dir / "Songs"
        songs_dir.mkdir()
        (songs_dir / "song1.mp3").write_text("music1")
        (songs_dir / "song2.mp3").write_text("music2")
        (songs_dir / "song3.mp3").write_text("music3")

        with patch.object(config, 'ROOT_DIR', str(temp_dir)):
            result = choose_random_song()

        assert result is not None
        assert "Songs" in result
        assert result.endswith((".mp3",)) or "song" in result

    def test_choose_random_song_multiple_calls(self, temp_dir):
        """Test that multiple calls can return different songs."""
        from utils import choose_random_song
        import config

        # Setup Songs directory with multiple files
        songs_dir = temp_dir / "Songs"
        songs_dir.mkdir()
        for i in range(10):
            (songs_dir / f"song{i}.mp3").write_text(f"music{i}")

        with patch.object(config, 'ROOT_DIR', str(temp_dir)):
            results = [choose_random_song() for _ in range(5)]

        # All results should be valid paths
        assert all(r is not None for r in results)
        # At least check they're in Songs directory
        assert all("Songs" in r for r in results)

    def test_choose_random_song_directory_not_found(self, temp_dir):
        """Test handling missing Songs directory."""
        from utils import choose_random_song
        import config

        with patch.object(config, 'ROOT_DIR', str(temp_dir)):
            result = choose_random_song()

        assert result is None

    def test_choose_random_song_empty_directory(self, temp_dir):
        """Test handling empty Songs directory."""
        from utils import choose_random_song
        import config

        # Create empty Songs directory
        songs_dir = temp_dir / "Songs"
        songs_dir.mkdir()

        with patch.object(config, 'ROOT_DIR', str(temp_dir)):
            result = choose_random_song()

        assert result is None

    def test_choose_random_song_single_file(self, temp_dir):
        """Test choosing song when only one file exists."""
        from utils import choose_random_song
        import config

        # Setup Songs directory with single file
        songs_dir = temp_dir / "Songs"
        songs_dir.mkdir()
        (songs_dir / "only_song.mp3").write_text("music")

        with patch.object(config, 'ROOT_DIR', str(temp_dir)):
            result = choose_random_song()

        assert result is not None
        assert "only_song.mp3" in result
