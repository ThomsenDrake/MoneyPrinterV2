"""
LLM Response Caching Service.

This module provides caching for LLM (Large Language Model) responses to:
- Reduce API costs by avoiding duplicate requests
- Improve response times for repeated prompts
- Enable offline operation for previously cached prompts
"""

import hashlib
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

from config import ROOT_DIR
from exceptions import CacheError


class LLMCache:
    """
    Cache for LLM responses with TTL (time-to-live) support.

    This class provides a file-based cache for LLM responses, enabling:
    - Reduced API costs through response reuse
    - Faster responses for repeated prompts
    - Optional TTL for cache expiration
    """

    def __init__(self, cache_dir: Optional[str] = None, default_ttl: Optional[int] = None):
        """
        Initialize the LLM cache.

        Args:
            cache_dir: Directory to store cache files. Defaults to ROOT_DIR/cache/llm_responses
            default_ttl: Default time-to-live in seconds. None means cache never expires.
        """
        if cache_dir is None:
            cache_dir = os.path.join(ROOT_DIR, "cache", "llm_responses")

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl = default_ttl
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"LLM cache initialized at: {self.cache_dir}")

    def _get_cache_key(self, prompt: str, model: Optional[str] = None, **kwargs) -> str:
        """
        Generate a cache key from prompt and parameters.

        Args:
            prompt: The LLM prompt
            model: Optional model identifier
            **kwargs: Additional parameters that affect the response

        Returns:
            A unique cache key (SHA256 hash)
        """
        # Create a stable representation of the cache key components
        key_data = {
            "prompt": prompt,
            "model": model,
            "kwargs": sorted(kwargs.items()),  # Sort for stable hashing
        }

        # Convert to JSON and hash
        key_json = json.dumps(key_data, sort_keys=True)
        cache_key = hashlib.sha256(key_json.encode("utf-8")).hexdigest()

        return cache_key

    def _get_cache_path(self, cache_key: str) -> Path:
        """
        Get the file path for a cache key.

        Args:
            cache_key: The cache key

        Returns:
            Path to the cache file
        """
        return self.cache_dir / f"{cache_key}.json"

    def get(self, prompt: str, model: Optional[str] = None, **kwargs) -> Optional[str]:
        """
        Retrieve a cached LLM response.

        Args:
            prompt: The LLM prompt
            model: Optional model identifier
            **kwargs: Additional parameters that affect the response

        Returns:
            The cached response or None if not found/expired
        """
        cache_key = self._get_cache_key(prompt, model, **kwargs)
        cache_path = self._get_cache_path(cache_key)

        if not cache_path.exists():
            self.logger.debug(f"Cache miss for key: {cache_key[:16]}...")
            return None

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache_data = json.load(f)

            # Check if cache has expired
            if "expires_at" in cache_data and cache_data["expires_at"] is not None:
                expires_at = datetime.fromisoformat(cache_data["expires_at"])
                if datetime.now() > expires_at:
                    self.logger.debug(f"Cache expired for key: {cache_key[:16]}...")
                    # Clean up expired cache
                    cache_path.unlink()
                    return None

            response = cache_data.get("response")
            self.logger.info(f"Cache hit for key: {cache_key[:16]}...")
            return response

        except (json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f"Invalid cache file {cache_path}: {str(e)}")
            # Delete corrupted cache file
            try:
                cache_path.unlink()
            except OSError:
                pass
            return None

    def set(
        self,
        prompt: str,
        response: str,
        model: Optional[str] = None,
        ttl: Optional[int] = None,
        **kwargs,
    ) -> None:
        """
        Store an LLM response in cache.

        Args:
            prompt: The LLM prompt
            response: The LLM response to cache
            model: Optional model identifier
            ttl: Time-to-live in seconds (overrides default_ttl). None means never expire.
            **kwargs: Additional parameters that affect the response

        Raises:
            CacheError: If caching fails
        """
        cache_key = self._get_cache_key(prompt, model, **kwargs)
        cache_path = self._get_cache_path(cache_key)

        # Calculate expiration time
        ttl_to_use = ttl if ttl is not None else self.default_ttl
        expires_at = None
        if ttl_to_use is not None:
            expires_at = (datetime.now() + timedelta(seconds=ttl_to_use)).isoformat()

        cache_data = {
            "prompt": prompt,
            "model": model,
            "response": response,
            "cached_at": datetime.now().isoformat(),
            "expires_at": expires_at,
            "kwargs": kwargs,
        }

        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)

            self.logger.debug(
                f"Cached response for key: {cache_key[:16]}... "
                f"(expires: {expires_at or 'never'})"
            )

        except (OSError, IOError) as e:
            self.logger.error(f"Failed to write cache file {cache_path}: {str(e)}")
            raise CacheError(f"Failed to cache LLM response: {str(e)}") from e

    def delete(self, prompt: str, model: Optional[str] = None, **kwargs) -> bool:
        """
        Delete a cached response.

        Args:
            prompt: The LLM prompt
            model: Optional model identifier
            **kwargs: Additional parameters that affect the response

        Returns:
            True if cache was deleted, False if it didn't exist
        """
        cache_key = self._get_cache_key(prompt, model, **kwargs)
        cache_path = self._get_cache_path(cache_key)

        if cache_path.exists():
            try:
                cache_path.unlink()
                self.logger.debug(f"Deleted cache for key: {cache_key[:16]}...")
                return True
            except OSError as e:
                self.logger.warning(f"Failed to delete cache file {cache_path}: {str(e)}")
                return False
        return False

    def clear(self) -> int:
        """
        Clear all cached responses.

        Returns:
            Number of cache files deleted
        """
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
                count += 1
            except OSError as e:
                self.logger.warning(f"Failed to delete {cache_file}: {str(e)}")

        self.logger.info(f"Cleared {count} cache files")
        return count

    def clear_expired(self) -> int:
        """
        Clear only expired cache entries.

        Returns:
            Number of expired cache files deleted
        """
        count = 0
        now = datetime.now()

        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)

                # Check if expired
                if "expires_at" in cache_data and cache_data["expires_at"] is not None:
                    expires_at = datetime.fromisoformat(cache_data["expires_at"])
                    if now > expires_at:
                        cache_file.unlink()
                        count += 1

            except (json.JSONDecodeError, KeyError, OSError) as e:
                self.logger.warning(f"Error processing {cache_file}: {str(e)}")
                # Delete corrupted files
                try:
                    cache_file.unlink()
                    count += 1
                except OSError:
                    pass

        self.logger.info(f"Cleared {count} expired cache files")
        return count

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_files = 0
        expired_files = 0
        total_size = 0
        now = datetime.now()

        for cache_file in self.cache_dir.glob("*.json"):
            total_files += 1
            total_size += cache_file.stat().st_size

            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)

                if "expires_at" in cache_data and cache_data["expires_at"] is not None:
                    expires_at = datetime.fromisoformat(cache_data["expires_at"])
                    if now > expires_at:
                        expired_files += 1

            except (json.JSONDecodeError, KeyError, OSError):
                pass

        return {
            "total_entries": total_files,
            "expired_entries": expired_files,
            "valid_entries": total_files - expired_files,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "cache_dir": str(self.cache_dir),
        }


# Global singleton instance for easy access
_default_cache: Optional[LLMCache] = None


def get_llm_cache(cache_dir: Optional[str] = None, default_ttl: Optional[int] = None) -> LLMCache:
    """
    Get the default LLM cache instance (singleton pattern).

    Args:
        cache_dir: Optional cache directory (only used on first call)
        default_ttl: Optional default TTL in seconds (only used on first call)

    Returns:
        The global LLM cache instance
    """
    global _default_cache

    if _default_cache is None:
        _default_cache = LLMCache(cache_dir=cache_dir, default_ttl=default_ttl)

    return _default_cache
