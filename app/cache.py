"""Caching layer for ERP Paraguay.

This module provides a simple caching mechanism to reduce database queries
for frequently accessed, rarely-changing data.
"""
import logging
import functools
import time
from typing import Any, Callable, Dict, Optional, TypeVar, Tuple
from threading import Lock
from app.config import ENVIRONMENT

logger = logging.getLogger(__name__)

# Cache configuration by data type
CACHE_TTL = {
    'categories': 3600,      # 1 hour
    'products': 300,         # 5 minutes
    'customers': 600,        # 10 minutes
    'suppliers': 600,        # 10 minutes
    'settings': 1800,        # 30 minutes
    'tax_rates': 86400,      # 24 hours
    'default': 300,          # 5 minutes
}

# Disable cache in development or test environments
CACHE_ENABLED = ENVIRONMENT == 'production'

# Type variable for cached functions
T = TypeVar('T')


class CacheEntry:
    """Represents a single cache entry with value and expiration."""

    def __init__(self, value: Any, ttl: int):
        """Initialize cache entry.

        Args:
            value: The cached value
            ttl: Time to live in seconds
        """
        self.value = value
        self.expiry = time.time() + ttl

    def is_expired(self) -> bool:
        """Check if cache entry has expired.

        Returns:
            True if expired, False otherwise
        """
        return time.time() > self.expiry


class SimpleCache:
    """Simple thread-safe in-memory cache with TTL support.

    This cache stores data in memory with configurable time-to-live (TTL).
    It's designed for single-process applications. For multi-process deployments,
    consider using Redis or Memcached.

    Attributes:
        enabled: Whether caching is enabled
        hits: Number of cache hits
        misses: Number of cache misses
    """

    def __init__(self, enabled: bool = True):
        """Initialize the cache.

        Args:
            enabled: Whether caching should be enabled
        """
        self.enabled = enabled and CACHE_ENABLED
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = Lock()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value if exists and not expired, None otherwise
        """
        if not self.enabled:
            return None

        with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                self._misses += 1
                logger.debug(f"Cache miss: {key}")
                return None

            if entry.is_expired():
                # Remove expired entry
                del self._cache[key]
                self._misses += 1
                logger.debug(f"Cache expired: {key}")
                return None

            self._hits += 1
            logger.debug(f"Cache hit: {key}")
            return entry.value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (optional, uses default if not specified)
        """
        if not self.enabled:
            return

        if ttl is None:
            ttl = CACHE_TTL['default']

        with self._lock:
            self._cache[key] = CacheEntry(value, ttl)
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")

    def delete(self, key: str) -> bool:
        """Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted, False if not found
        """
        if not self.enabled:
            return False

        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Cache deleted: {key}")
                return True
            return False

    def clear(self) -> None:
        """Clear all cache entries."""
        if not self.enabled:
            return

        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"Cache cleared: {count} entries")

    def cleanup_expired(self) -> int:
        """Remove all expired entries from cache.

        Returns:
            Number of entries removed
        """
        if not self.enabled:
            return 0

        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]

            for key in expired_keys:
                del self._cache[key]

            if expired_keys:
                logger.info(f"Cache cleanup: removed {len(expired_keys)} expired entries")

            return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats:
                - enabled: Whether cache is enabled
                - size: Current number of entries
                - hits: Number of cache hits
                - misses: Number of cache misses
                - hit_rate: Cache hit rate (0.0 to 1.0)
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0

            return {
                'enabled': self.enabled,
                'size': len(self._cache),
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': hit_rate
            }


# Global cache instance
_global_cache = SimpleCache()


def get_cache() -> SimpleCache:
    """Get the global cache instance.

    Returns:
        Global SimpleCache instance
    """
    return _global_cache


def cached(
    cache_type: str = 'default',
    key_func: Optional[Callable[..., str]] = None,
    ttl: Optional[int] = None
) -> Callable:
    """Decorator to cache function results.

    Args:
        cache_type: Type of cache (determines default TTL)
        key_func: Optional function to generate cache key from arguments
        ttl: Optional custom TTL in seconds

    Returns:
        Decorated function with caching

    Example:
        @cached('categories')
        def get_categories():
            return db.query(Category).all()

        @cached('products', key_func=lambda id: f'product:{id}')
        def get_product_by_id(product_id: int):
            return db.query(Product).get(product_id)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                args_str = '_'.join(str(a) for a in args)
                kwargs_str = '_'.join(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = f"{func.__name__}:{args_str}:{kwargs_str}"

            # Try to get from cache
            cached_value = _global_cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Call function and cache result
            result = func(*args, **kwargs)
            cache_ttl = ttl or CACHE_TTL.get(cache_type, CACHE_TTL['default'])
            _global_cache.set(cache_key, result, cache_ttl)

            return result

        # Add cache management methods to wrapped function
        wrapper.cache_key = lambda *args, **kwargs: (
            key_func(*args, **kwargs) if key_func else
            f"{func.__name__}:{args}"
        )
        wrapper.cache_clear = lambda: _global_cache.clear()
        wrapper.cache_delete = lambda *args, **kwargs: (
            _global_cache.delete(wrapper.cache_key(*args, **kwargs))
        )
        wrapper.cache_stats = lambda: _global_cache.get_stats()

        return wrapper

    return decorator


def invalidate_pattern(pattern: str) -> int:
    """Invalidate all cache entries matching a pattern.

    Args:
        pattern: Cache key pattern to match (simple substring match)

    Returns:
        Number of entries invalidated

    Example:
        # Invalidate all product caches
        invalidate_pattern('product:')

        # Invalidate all category caches
        invalidate_pattern('get_categories')
    """
    if not _global_cache.enabled:
        return 0

    with _global_cache._lock:
        keys_to_delete = [
            key for key in _global_cache._cache.keys()
            if pattern in key
        ]

        for key in keys_to_delete:
            del _global_cache._cache[key]

        if keys_to_delete:
            logger.info(f"Invalidated {len(keys_to_delete)} cache entries matching '{pattern}'")

        return len(keys_to_delete)


def warmup_cache() -> None:
    """Warm up cache by preloading common data.

    This function should be called during application startup to load
    frequently-accessed data into cache.

    Example:
        from app.cache import warmup_cache
        from app.services.category_service import list_categories

        def startup():
            warmup_cache()
    """
    logger.info("Starting cache warmup...")

    try:
        # Import here to avoid circular dependencies
        from app.services.category_service import list_categories

        # Cache categories (long TTL)
        categories = list_categories(active_only=True)
        _global_cache.set('categories:all', categories, CACHE_TTL['categories'])
        logger.info(f"Cached {len(categories)} categories")

        # Log cache stats after warmup
        stats = _global_cache.get_stats()
        logger.info(f"Cache warmup complete. Stats: {stats}")

    except Exception as e:
        logger.warning(f"Cache warmup failed: {e}", exc_info=True)


# Background cleanup task
def start_cache_cleanup_task(interval_seconds: int = 300) -> None:
    """Start background task to periodically clean up expired cache entries.

    Args:
        interval_seconds: Interval between cleanups (default: 5 minutes)

    Note:
        This is a simple implementation using a loop. In production,
        consider using a proper task scheduler like Celery beat.
    """
    import threading

    def cleanup_loop():
        while True:
            try:
                time.sleep(interval_seconds)
                removed = _global_cache.cleanup_expired()
                if removed > 0:
                    logger.info(f"Background cache cleanup: removed {removed} expired entries")
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}", exc_info=True)

    if _global_cache.enabled:
        cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        cleanup_thread.start()
        logger.info(f"Started cache cleanup task (interval: {interval_seconds}s)")
