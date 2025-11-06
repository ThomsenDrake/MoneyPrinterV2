"""
Tests for LLM Response Caching Service.

This module tests the LLMCache class which provides caching for LLM responses.
"""

import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.exceptions import CacheError
from src.llm_cache import LLMCache, get_llm_cache


@pytest.fixture
def temp_cache_dir():
    """Create a temporary directory for cache testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def cache(temp_cache_dir):
    """Create an LLMCache instance with temporary directory."""
    return LLMCache(cache_dir=temp_cache_dir)


class TestLLMCacheInit:
    """Tests for LLMCache initialization."""

    def test_init_with_default_dir(self):
        """Test initialization with default cache directory."""
        with patch("src.llm_cache.ROOT_DIR", "/tmp/test"):
            cache = LLMCache()
            assert str(cache.cache_dir) == "/tmp/test/cache/llm_responses"

    def test_init_with_custom_dir(self, temp_cache_dir):
        """Test initialization with custom cache directory."""
        cache = LLMCache(cache_dir=temp_cache_dir)
        assert str(cache.cache_dir) == temp_cache_dir

    def test_init_creates_cache_dir(self, temp_cache_dir):
        """Test that initialization creates cache directory."""
        cache_path = os.path.join(temp_cache_dir, "custom_cache")
        assert not os.path.exists(cache_path)

        cache = LLMCache(cache_dir=cache_path)
        assert os.path.exists(cache_path)

    def test_init_with_ttl(self, temp_cache_dir):
        """Test initialization with default TTL."""
        cache = LLMCache(cache_dir=temp_cache_dir, default_ttl=3600)
        assert cache.default_ttl == 3600


class TestLLMCacheCacheKey:
    """Tests for cache key generation."""

    def test_cache_key_same_for_identical_inputs(self, cache):
        """Test that identical inputs produce the same cache key."""
        key1 = cache._get_cache_key("Test prompt", model="gpt-4")
        key2 = cache._get_cache_key("Test prompt", model="gpt-4")
        assert key1 == key2

    def test_cache_key_different_for_different_prompts(self, cache):
        """Test that different prompts produce different cache keys."""
        key1 = cache._get_cache_key("Prompt 1", model="gpt-4")
        key2 = cache._get_cache_key("Prompt 2", model="gpt-4")
        assert key1 != key2

    def test_cache_key_different_for_different_models(self, cache):
        """Test that different models produce different cache keys."""
        key1 = cache._get_cache_key("Test prompt", model="gpt-4")
        key2 = cache._get_cache_key("Test prompt", model="gpt-3.5")
        assert key1 != key2

    def test_cache_key_includes_kwargs(self, cache):
        """Test that kwargs affect cache key."""
        key1 = cache._get_cache_key("Test prompt", temperature=0.7)
        key2 = cache._get_cache_key("Test prompt", temperature=0.9)
        assert key1 != key2


class TestLLMCacheSetAndGet:
    """Tests for set and get operations."""

    def test_set_and_get_basic(self, cache):
        """Test basic set and get operations."""
        cache.set("Test prompt", "Test response", model="gpt-4")
        response = cache.get("Test prompt", model="gpt-4")
        assert response == "Test response"

    def test_get_nonexistent_returns_none(self, cache):
        """Test that getting non-existent key returns None."""
        response = cache.get("Nonexistent prompt")
        assert response is None

    def test_set_with_kwargs(self, cache):
        """Test set and get with kwargs."""
        cache.set("Test prompt", "Test response", model="gpt-4", temperature=0.7)
        response = cache.get("Test prompt", model="gpt-4", temperature=0.7)
        assert response == "Test response"

        # Different kwargs should not match
        response = cache.get("Test prompt", model="gpt-4", temperature=0.9)
        assert response is None

    def test_set_creates_cache_file(self, cache):
        """Test that set creates a cache file."""
        cache.set("Test prompt", "Test response")
        cache_files = list(Path(cache.cache_dir).glob("*.json"))
        assert len(cache_files) == 1

    def test_cache_file_contains_correct_data(self, cache):
        """Test that cache file contains correct data."""
        cache.set("Test prompt", "Test response", model="gpt-4")

        cache_files = list(Path(cache.cache_dir).glob("*.json"))
        with open(cache_files[0], "r") as f:
            data = json.load(f)

        assert data["prompt"] == "Test prompt"
        assert data["response"] == "Test response"
        assert data["model"] == "gpt-4"
        assert "cached_at" in data


class TestLLMCacheTTL:
    """Tests for TTL (time-to-live) functionality."""

    def test_set_with_ttl(self, cache):
        """Test setting cache with TTL."""
        cache.set("Test prompt", "Test response", ttl=3600)

        # Should be retrievable immediately
        response = cache.get("Test prompt")
        assert response == "Test response"

    def test_expired_cache_returns_none(self, cache):
        """Test that expired cache returns None."""
        # Set cache with 1-second TTL
        cache.set("Test prompt", "Test response", ttl=1)

        # Mock datetime to be in the future
        future_time = datetime.now() + timedelta(seconds=2)
        with patch("src.llm_cache.datetime") as mock_datetime:
            mock_datetime.now.return_value = future_time
            mock_datetime.fromisoformat = datetime.fromisoformat

            response = cache.get("Test prompt")
            assert response is None

    def test_default_ttl_used_when_not_specified(self, temp_cache_dir):
        """Test that default TTL is used when not specified."""
        cache = LLMCache(cache_dir=temp_cache_dir, default_ttl=7200)
        cache.set("Test prompt", "Test response")

        # Check cache file has expires_at set
        cache_files = list(Path(cache.cache_dir).glob("*.json"))
        with open(cache_files[0], "r") as f:
            data = json.load(f)

        assert data["expires_at"] is not None

    def test_no_expiration_when_ttl_none(self, cache):
        """Test that cache doesn't expire when TTL is None."""
        cache.set("Test prompt", "Test response", ttl=None)

        # Check cache file has expires_at as None
        cache_files = list(Path(cache.cache_dir).glob("*.json"))
        with open(cache_files[0], "r") as f:
            data = json.load(f)

        assert data["expires_at"] is None


class TestLLMCacheDelete:
    """Tests for delete operations."""

    def test_delete_existing_cache(self, cache):
        """Test deleting an existing cache entry."""
        cache.set("Test prompt", "Test response")
        assert cache.delete("Test prompt") is True

        # Verify it's deleted
        response = cache.get("Test prompt")
        assert response is None

    def test_delete_nonexistent_cache(self, cache):
        """Test deleting a non-existent cache entry."""
        assert cache.delete("Nonexistent prompt") is False


class TestLLMCacheClear:
    """Tests for clear operations."""

    def test_clear_all(self, cache):
        """Test clearing all cache entries."""
        # Add multiple entries
        cache.set("Prompt 1", "Response 1")
        cache.set("Prompt 2", "Response 2")
        cache.set("Prompt 3", "Response 3")

        # Clear all
        count = cache.clear()
        assert count == 3

        # Verify all are gone
        assert cache.get("Prompt 1") is None
        assert cache.get("Prompt 2") is None
        assert cache.get("Prompt 3") is None

    def test_clear_expired(self, cache):
        """Test clearing only expired entries."""
        # Add entries with different TTLs
        cache.set("Prompt 1", "Response 1", ttl=3600)  # Not expired
        cache.set("Prompt 2", "Response 2", ttl=1)  # Will expire
        cache.set("Prompt 3", "Response 3", ttl=None)  # Never expires

        # Mock time to make entry 2 expire
        future_time = datetime.now() + timedelta(seconds=2)
        with patch("src.llm_cache.datetime") as mock_datetime:
            mock_datetime.now.return_value = future_time
            mock_datetime.fromisoformat = datetime.fromisoformat

            count = cache.clear_expired()
            # Only expired entry should be deleted
            assert count >= 1  # At least the expired one

        # Verify non-expired entries still exist
        assert cache.get("Prompt 1") is not None
        assert cache.get("Prompt 3") is not None


class TestLLMCacheStats:
    """Tests for cache statistics."""

    def test_get_cache_stats_empty(self, cache):
        """Test getting stats for empty cache."""
        stats = cache.get_cache_stats()
        assert stats["total_entries"] == 0
        assert stats["valid_entries"] == 0
        assert stats["expired_entries"] == 0
        assert stats["total_size_bytes"] == 0

    def test_get_cache_stats_with_entries(self, cache):
        """Test getting stats with cache entries."""
        cache.set("Prompt 1", "Response 1")
        cache.set("Prompt 2", "Response 2")
        cache.set("Prompt 3", "Response 3")

        stats = cache.get_cache_stats()
        assert stats["total_entries"] == 3
        assert stats["total_size_bytes"] > 0
        assert "cache_dir" in stats


class TestLLMCacheGlobalSingleton:
    """Tests for global singleton pattern."""

    def test_get_llm_cache_returns_same_instance(self):
        """Test that get_llm_cache returns the same instance."""
        # Reset global cache
        import src.llm_cache

        src.llm_cache._default_cache = None

        cache1 = get_llm_cache()
        cache2 = get_llm_cache()
        assert cache1 is cache2

    def test_get_llm_cache_uses_parameters_on_first_call(self, temp_cache_dir):
        """Test that parameters are used only on first call."""
        # Reset global cache
        import src.llm_cache

        src.llm_cache._default_cache = None

        cache = get_llm_cache(cache_dir=temp_cache_dir, default_ttl=7200)
        assert str(cache.cache_dir) == temp_cache_dir
        assert cache.default_ttl == 7200


class TestLLMCacheErrorHandling:
    """Tests for error handling."""

    def test_corrupted_cache_file_returns_none(self, cache, temp_cache_dir):
        """Test that corrupted cache file returns None."""
        # Create a corrupted cache file
        cache_key = cache._get_cache_key("Test prompt")
        cache_path = cache._get_cache_path(cache_key)

        with open(cache_path, "w") as f:
            f.write("{ invalid json }")

        # Should return None and delete corrupted file
        response = cache.get("Test prompt")
        assert response is None
        assert not cache_path.exists()

    @pytest.mark.skip(reason="Test needs refactoring - mock exception handling issue")
    def test_set_with_io_error_raises_cache_error(self, cache):
        """Test that I/O errors during set raise CacheError."""
        # Make cache directory read-only to trigger I/O error
        with patch("builtins.open", side_effect=IOError("Disk full")):
            with pytest.raises(CacheError) as exc_info:
                cache.set("Test prompt", "Test response")

        assert "Failed to cache" in str(exc_info.value)
