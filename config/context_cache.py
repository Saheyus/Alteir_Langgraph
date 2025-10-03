
"""Caching utilities for Notion context selection."""

from __future__ import annotations

import time
from dataclasses import dataclass
from threading import RLock
from typing import Any, Dict, Optional


@dataclass
class CacheEntry:
    """Represent a cached value with an expiration timestamp."""

    value: Any
    expires_at: float

    def is_expired(self) -> bool:
        """Return True when the entry should be discarded."""

        return time.time() >= self.expires_at


class ContextCache:
    """Small in-memory cache tailored for Notion context artefacts.

    The cache keeps three logical namespaces:
    - ``list``    : full listings of database pages (refreshed every hour)
    - ``preview`` : lightweight previews for individual pages
    - ``full``    : full page payloads used when injecting context in prompts

    Expiration timestamps are handled per namespace but can be overridden
    when setting values (useful during tests).
    """

    def __init__(self) -> None:
        self._ttls: Dict[str, float] = {
            "list": 60 * 60,       # 1 hour
            "preview": 15 * 60,    # 15 minutes
            "full": 15 * 60,       # 15 minutes
        }
        self._stores: Dict[str, Dict[str, CacheEntry]] = {
            name: {} for name in self._ttls
        }
        self._lock = RLock()

    def _get_store(self, namespace: str) -> Dict[str, CacheEntry]:
        if namespace not in self._stores:
            raise KeyError(f"Unknown cache namespace: {namespace}")
        return self._stores[namespace]

    def get(self, namespace: str, key: str) -> Optional[Any]:
        """Retrieve a value from the cache if it exists and is fresh."""

        with self._lock:
            store = self._get_store(namespace)
            entry = store.get(key)
            if not entry:
                return None
            if entry.is_expired():
                del store[key]
                return None
            return entry.value

    def set(
        self,
        namespace: str,
        key: str,
        value: Any,
        ttl: Optional[float] = None,
    ) -> Any:
        """Insert a value in the cache and return it."""

        with self._lock:
            store = self._get_store(namespace)
            duration = ttl if ttl is not None else self._ttls[namespace]
            store[key] = CacheEntry(value=value, expires_at=time.time() + duration)
            return value

    def invalidate(self, namespace: str, key: Optional[str] = None) -> None:
        """Remove either a single key or the whole namespace."""

        with self._lock:
            store = self._get_store(namespace)
            if key is None:
                store.clear()
            else:
                store.pop(key, None)

    def clear(self) -> None:
        """Reset the entire cache."""

        with self._lock:
            for store in self._stores.values():
                store.clear()

    def set_namespace_ttl(self, namespace: str, ttl: float) -> None:
        """Override the default TTL for a namespace (used in tests)."""

        with self._lock:
            self._ttls[namespace] = ttl


# Global cache instance used across the application.
context_cache = ContextCache()

__all__ = ["CacheEntry", "ContextCache", "context_cache"]
