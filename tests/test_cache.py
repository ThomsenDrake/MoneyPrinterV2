"""
Unit tests for cache management (src/cache.py).
"""
import os
import json
import pytest
import platform
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path


class TestFileLock:
    """Tests for the FileLock context manager."""

    @pytest.mark.skipif(platform.system() == "Windows", reason="Unix-specific test")
    def test_file_lock_unix(self, temp_dir):
        """Test file locking on Unix systems."""
        import fcntl
        from cache import FileLock

        test_file = temp_dir / "test.json"
        test_file.write_text("{}")

        with open(test_file, 'r') as f:
            with patch.object(fcntl, 'flock') as mock_flock:
                with FileLock(f):
                    mock_flock.assert_called_once_with(f.fileno(), fcntl.LOCK_EX)

    @pytest.mark.skipif(platform.system() != "Windows", reason="Windows-specific test")
    def test_file_lock_windows(self, temp_dir):
        """Test file locking on Windows systems."""
        import msvcrt
        from cache import FileLock

        test_file = temp_dir / "test.json"
        test_file.write_text("{}")

        with open(test_file, 'r') as f:
            with patch.object(msvcrt, 'locking') as mock_locking:
                with FileLock(f):
                    mock_locking.assert_called_once_with(f.fileno(), msvcrt.LK_LOCK, 1)

    def test_file_lock_exception_handling(self, temp_dir):
        """Test that FileLock handles exceptions during locking."""
        from cache import FileLock

        test_file = temp_dir / "test.json"
        test_file.write_text("{}")

        with open(test_file, 'r') as f:
            if platform.system() == "Windows":
                import msvcrt
                with patch.object(msvcrt, 'locking', side_effect=IOError("Lock error")):
                    with pytest.raises(IOError):
                        with FileLock(f):
                            pass
            else:
                import fcntl
                with patch.object(fcntl, 'flock', side_effect=IOError("Lock error")):
                    with pytest.raises(IOError):
                        with FileLock(f):
                            pass


class TestAtomicOperations:
    """Tests for atomic JSON file operations."""

    def test_atomic_read_json_existing_file(self, temp_dir):
        """Test reading an existing JSON file."""
        from cache import _atomic_read_json

        test_file = temp_dir / "test.json"
        test_data = {"key": "value", "number": 42}
        with open(test_file, 'w') as f:
            json.dump(test_data, f)

        result = _atomic_read_json(str(test_file), {})
        assert result == test_data

    def test_atomic_read_json_nonexistent_file(self, temp_dir):
        """Test reading a nonexistent file returns default."""
        from cache import _atomic_read_json

        test_file = temp_dir / "nonexistent.json"
        default = {"default": True}

        result = _atomic_read_json(str(test_file), default)
        assert result == default

    def test_atomic_read_json_empty_file(self, temp_dir):
        """Test reading an empty file returns default."""
        from cache import _atomic_read_json

        test_file = temp_dir / "empty.json"
        test_file.write_text("")
        default = {"default": True}

        result = _atomic_read_json(str(test_file), default)
        assert result == default

    def test_atomic_read_json_invalid_json(self, temp_dir):
        """Test reading invalid JSON returns default."""
        from cache import _atomic_read_json

        test_file = temp_dir / "invalid.json"
        test_file.write_text("{invalid json")
        default = {"default": True}

        result = _atomic_read_json(str(test_file), default)
        assert result == default

    def test_atomic_write_json(self, temp_dir):
        """Test writing JSON to file."""
        from cache import _atomic_write_json

        test_file = temp_dir / "subdir" / "test.json"
        test_data = {"key": "value", "list": [1, 2, 3]}

        _atomic_write_json(str(test_file), test_data)

        assert test_file.exists()
        with open(test_file, 'r') as f:
            result = json.load(f)
        assert result == test_data

    def test_atomic_write_json_creates_directory(self, temp_dir):
        """Test that atomic_write_json creates parent directories."""
        from cache import _atomic_write_json

        test_file = temp_dir / "deep" / "nested" / "dir" / "test.json"
        test_data = {"created": True}

        _atomic_write_json(str(test_file), test_data)

        assert test_file.exists()
        assert test_file.parent.exists()

    def test_atomic_update_json(self, temp_dir):
        """Test updating JSON file."""
        from cache import _atomic_update_json

        test_file = temp_dir / "test.json"
        initial_data = {"count": 0, "items": []}
        with open(test_file, 'w') as f:
            json.dump(initial_data, f)

        def update_fn(data):
            data["count"] += 1
            data["items"].append("new_item")
            return data

        _atomic_update_json(str(test_file), update_fn, {})

        with open(test_file, 'r') as f:
            result = json.load(f)

        assert result["count"] == 1
        assert "new_item" in result["items"]

    def test_atomic_update_json_creates_new_file(self, temp_dir):
        """Test that atomic_update_json creates new file if doesn't exist."""
        from cache import _atomic_update_json

        test_file = temp_dir / "new_dir" / "test.json"
        default_data = {"initialized": True}

        def update_fn(data):
            data["updated"] = True
            return data

        _atomic_update_json(str(test_file), update_fn, default_data)

        assert test_file.exists()
        with open(test_file, 'r') as f:
            result = json.load(f)

        assert result["initialized"] is True
        assert result["updated"] is True


class TestCachePaths:
    """Tests for cache path functions."""

    def test_get_cache_path(self):
        """Test getting cache path."""
        from cache import get_cache_path
        import config

        with patch.object(config, 'ROOT_DIR', '/test/root'):
            result = get_cache_path()
            assert result == '/test/root/.mp'

    def test_get_youtube_cache_path(self):
        """Test getting YouTube cache path."""
        from cache import get_youtube_cache_path
        import config

        with patch.object(config, 'ROOT_DIR', '/test/root'):
            result = get_youtube_cache_path()
            assert result == '/test/root/.mp/youtube.json'

    def test_get_twitter_cache_path(self):
        """Test getting Twitter cache path."""
        from cache import get_twitter_cache_path
        import config

        with patch.object(config, 'ROOT_DIR', '/test/root'):
            result = get_twitter_cache_path()
            assert result == '/test/root/.mp/twitter.json'

    def test_get_afm_cache_path(self):
        """Test getting AFM cache path."""
        from cache import get_afm_cache_path
        import config

        with patch.object(config, 'ROOT_DIR', '/test/root'):
            result = get_afm_cache_path()
            assert result == '/test/root/.mp/afm.json'

    def test_get_results_cache_path(self):
        """Test getting results cache path."""
        from cache import get_results_cache_path
        import config

        with patch.object(config, 'ROOT_DIR', '/test/root'):
            result = get_results_cache_path()
            assert result == '/test/root/.mp/scraper_results.csv'


class TestAccountManagement:
    """Tests for account management functions."""

    def test_get_accounts_youtube(self, temp_dir):
        """Test getting YouTube accounts."""
        from cache import get_accounts
        import config

        # Setup
        cache_dir = temp_dir / ".mp"
        cache_dir.mkdir()
        youtube_cache = cache_dir / "youtube.json"

        test_accounts = [
            {"id": "123", "name": "Account 1"},
            {"id": "456", "name": "Account 2"}
        ]
        with open(youtube_cache, 'w') as f:
            json.dump({"accounts": test_accounts}, f)

        with patch.object(config, 'ROOT_DIR', str(temp_dir)):
            result = get_accounts("youtube")

        assert len(result) == 2
        assert result[0]["id"] == "123"
        assert result[1]["name"] == "Account 2"

    def test_get_accounts_twitter(self, temp_dir):
        """Test getting Twitter accounts."""
        from cache import get_accounts
        import config

        # Setup
        cache_dir = temp_dir / ".mp"
        cache_dir.mkdir()
        twitter_cache = cache_dir / "twitter.json"

        test_accounts = [{"id": "789", "handle": "@test"}]
        with open(twitter_cache, 'w') as f:
            json.dump({"accounts": test_accounts}, f)

        with patch.object(config, 'ROOT_DIR', str(temp_dir)):
            result = get_accounts("twitter")

        assert len(result) == 1
        assert result[0]["handle"] == "@test"

    def test_get_accounts_empty_cache(self, temp_dir):
        """Test getting accounts when cache is empty."""
        from cache import get_accounts
        import config

        with patch.object(config, 'ROOT_DIR', str(temp_dir)):
            result = get_accounts("youtube")

        assert result == []

    def test_get_accounts_unknown_provider(self):
        """Test getting accounts with unknown provider."""
        from cache import get_accounts

        result = get_accounts("unknown_provider")
        assert result == []

    def test_add_account_youtube(self, temp_dir):
        """Test adding YouTube account."""
        from cache import add_account, get_accounts
        import config

        # Setup
        cache_dir = temp_dir / ".mp"
        cache_dir.mkdir()

        with patch.object(config, 'ROOT_DIR', str(temp_dir)):
            new_account = {"id": "999", "name": "New Account"}
            add_account("youtube", new_account)

            accounts = get_accounts("youtube")

        assert len(accounts) == 1
        assert accounts[0]["id"] == "999"

    def test_add_account_multiple(self, temp_dir):
        """Test adding multiple accounts."""
        from cache import add_account, get_accounts
        import config

        # Setup
        cache_dir = temp_dir / ".mp"
        cache_dir.mkdir()

        with patch.object(config, 'ROOT_DIR', str(temp_dir)):
            add_account("twitter", {"id": "1", "name": "Account 1"})
            add_account("twitter", {"id": "2", "name": "Account 2"})

            accounts = get_accounts("twitter")

        assert len(accounts) == 2

    def test_remove_account(self, temp_dir):
        """Test removing account."""
        from cache import add_account, remove_account, get_accounts
        import config

        # Setup
        cache_dir = temp_dir / ".mp"
        cache_dir.mkdir()

        with patch.object(config, 'ROOT_DIR', str(temp_dir)):
            # Add accounts
            add_account("youtube", {"id": "1", "name": "Account 1"})
            add_account("youtube", {"id": "2", "name": "Account 2"})
            add_account("youtube", {"id": "3", "name": "Account 3"})

            # Remove one
            remove_account("youtube", "2")

            accounts = get_accounts("youtube")

        assert len(accounts) == 2
        assert not any(acc["id"] == "2" for acc in accounts)
        assert any(acc["id"] == "1" for acc in accounts)
        assert any(acc["id"] == "3" for acc in accounts)

    def test_remove_account_unknown_provider(self, temp_dir):
        """Test removing account with unknown provider."""
        from cache import remove_account

        # Should not raise exception
        remove_account("unknown_provider", "123")


class TestProductManagement:
    """Tests for product management functions."""

    def test_get_products_empty(self, temp_dir):
        """Test getting products when cache is empty."""
        from cache import get_products
        import config

        with patch.object(config, 'ROOT_DIR', str(temp_dir)):
            result = get_products()

        assert result == []

    def test_add_product(self, temp_dir):
        """Test adding product."""
        from cache import add_product, get_products
        import config

        # Setup
        cache_dir = temp_dir / ".mp"
        cache_dir.mkdir()

        with patch.object(config, 'ROOT_DIR', str(temp_dir)):
            new_product = {"id": "prod123", "name": "Test Product", "price": 99.99}
            add_product(new_product)

            products = get_products()

        assert len(products) == 1
        assert products[0]["id"] == "prod123"
        assert products[0]["price"] == 99.99

    def test_add_multiple_products(self, temp_dir):
        """Test adding multiple products."""
        from cache import add_product, get_products
        import config

        # Setup
        cache_dir = temp_dir / ".mp"
        cache_dir.mkdir()

        with patch.object(config, 'ROOT_DIR', str(temp_dir)):
            add_product({"id": "1", "name": "Product 1"})
            add_product({"id": "2", "name": "Product 2"})
            add_product({"id": "3", "name": "Product 3"})

            products = get_products()

        assert len(products) == 3
        assert products[0]["id"] == "1"
        assert products[2]["name"] == "Product 3"
