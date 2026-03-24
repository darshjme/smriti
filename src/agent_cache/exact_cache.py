"""ExactCache — hash-based exact match cache with TTL and LRU eviction."""

import hashlib
import time
from collections import OrderedDict
from typing import Optional


class ExactCache:
    """Hash-based exact match cache for LLM responses.

    Uses SHA-256 to fingerprint prompts and stores responses with TTL.
    Evicts LRU entries when max_size is exceeded.

    Args:
        max_size: Maximum number of entries to hold (LRU eviction).
        ttl_seconds: Time-to-live for each entry in seconds.
    """

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600) -> None:
        if max_size < 1:
            raise ValueError("max_size must be >= 1")
        if ttl_seconds < 0:
            raise ValueError("ttl_seconds must be >= 0")
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        # OrderedDict used as LRU store: key -> (response, stored_at)
        self._store: OrderedDict[str, tuple[str, float]] = OrderedDict()
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _hash(prompt: str) -> str:
        return hashlib.sha256(prompt.encode("utf-8")).hexdigest()

    def _is_expired(self, stored_at: float) -> bool:
        if self.ttl_seconds == 0:
            return False
        return (time.monotonic() - stored_at) > self.ttl_seconds

    def _evict_expired(self) -> None:
        """Remove all expired entries."""
        expired_keys = [
            k for k, (_, ts) in list(self._store.items()) if self._is_expired(ts)
        ]
        for k in expired_keys:
            del self._store[k]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, prompt: str) -> Optional[str]:
        """Return cached response for *prompt*, or None on miss/expiry."""
        key = self._hash(prompt)
        if key not in self._store:
            self._misses += 1
            return None
        response, stored_at = self._store[key]
        if self._is_expired(stored_at):
            del self._store[key]
            self._misses += 1
            return None
        # Move to end = most recently used
        self._store.move_to_end(key)
        self._hits += 1
        return response

    def set(self, prompt: str, response: str) -> None:
        """Store *response* for *prompt* with the configured TTL."""
        key = self._hash(prompt)
        if key in self._store:
            self._store.move_to_end(key)
        self._store[key] = (response, time.monotonic())
        # Evict LRU if over capacity
        while len(self._store) > self.max_size:
            self._store.popitem(last=False)
            self._evictions += 1

    def invalidate(self, prompt: str) -> bool:
        """Remove entry for *prompt*. Returns True if it existed."""
        key = self._hash(prompt)
        if key in self._store:
            del self._store[key]
            return True
        return False

    def clear(self) -> None:
        """Remove all entries."""
        self._store.clear()

    def stats(self) -> dict:
        """Return cache statistics."""
        self._evict_expired()
        total = self._hits + self._misses
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self._hits / total if total else 0.0,
            "size": len(self._store),
            "evictions": self._evictions,
        }
