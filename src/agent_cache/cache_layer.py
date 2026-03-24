"""CacheLayer — unified exact + semantic cache with decorator support."""

import functools
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from .exact_cache import ExactCache
from .semantic_cache import SemanticCache


@dataclass
class CacheResult:
    """Metadata-rich result returned by CacheLayer.get().

    Attributes:
        response:    The cached LLM response string.
        cache_type:  "exact" if returned from ExactCache, "semantic" otherwise.
        similarity:  Cosine similarity score (None for exact hits).
        age_seconds: Approximate age of the cached entry in seconds.
    """

    response: str
    cache_type: str  # "exact" | "semantic"
    similarity: Optional[float] = field(default=None)
    age_seconds: float = field(default=0.0)

    def __post_init__(self) -> None:
        if self.cache_type not in ("exact", "semantic"):
            raise ValueError(f"cache_type must be 'exact' or 'semantic', got {self.cache_type!r}")
        if self.similarity is not None and not (0.0 <= self.similarity <= 1.0):
            raise ValueError("similarity must be between 0 and 1")
        if self.age_seconds < 0:
            raise ValueError("age_seconds must be >= 0")


class CacheLayer:
    """Unified caching layer that checks exact match first, then semantic.

    Usage::

        exact = ExactCache(max_size=1000, ttl_seconds=3600)
        semantic = SemanticCache(threshold=0.85, max_size=500, ttl_seconds=7200)
        cache = CacheLayer(exact, semantic)

        # Manual use
        cache.set("What is Python?", "Python is a programming language.")
        result = cache.get("What is Python?")  # CacheResult(cache_type="exact", ...)

        # Decorator use
        @cache.wrap
        def call_llm(prompt: str) -> str:
            return expensive_api_call(prompt)

    Args:
        exact:    Configured ExactCache instance.
        semantic: Configured SemanticCache instance.
    """

    def __init__(self, exact: ExactCache, semantic: SemanticCache) -> None:
        self.exact = exact
        self.semantic = semantic
        self._exact_hits = 0
        self._semantic_hits = 0
        self._misses = 0
        self._start_time = time.monotonic()

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def get(self, prompt: str) -> Optional[CacheResult]:
        """Return a CacheResult or None if no suitable cache entry exists.

        Checks ExactCache first (O(1)), then SemanticCache.
        """
        t0 = time.monotonic()

        # 1. Exact match
        exact_response = self.exact.get(prompt)
        if exact_response is not None:
            self._exact_hits += 1
            return CacheResult(
                response=exact_response,
                cache_type="exact",
                similarity=None,
                age_seconds=time.monotonic() - t0,
            )

        # 2. Semantic match
        sem_result = self.semantic.get(prompt)
        if sem_result is not None:
            response, similarity = sem_result
            self._semantic_hits += 1
            return CacheResult(
                response=response,
                cache_type="semantic",
                similarity=similarity,
                age_seconds=time.monotonic() - t0,
            )

        self._misses += 1
        return None

    def set(self, prompt: str, response: str) -> None:
        """Store *response* in both caches simultaneously."""
        self.exact.set(prompt, response)
        self.semantic.set(prompt, response)

    def wrap(self, llm_func: Callable[[str], str]) -> Callable[[str], str]:
        """Decorator that transparently caches LLM function calls.

        The wrapped function must accept a single positional *prompt* argument
        and return a string response.

        Example::

            @cache.wrap
            def gpt(prompt: str) -> str:
                return openai.chat(prompt)

        """

        @functools.wraps(llm_func)
        def wrapper(prompt: str) -> str:
            result = self.get(prompt)
            if result is not None:
                return result.response
            response = llm_func(prompt)
            self.set(prompt, response)
            return response

        return wrapper

    def stats(self) -> dict:
        """Return combined statistics across both caches."""
        total_saved = self._exact_hits + self._semantic_hits
        total_calls = total_saved + self._misses
        exact_stats = self.exact.stats()
        sem_stats = self.semantic.stats()
        return {
            "exact_hits": self._exact_hits,
            "semantic_hits": self._semantic_hits,
            "misses": self._misses,
            "total_saved_calls": total_saved,
            "total_calls": total_calls,
            "overall_hit_rate": total_saved / total_calls if total_calls else 0.0,
            "exact_cache": exact_stats,
            "semantic_cache": sem_stats,
            "uptime_seconds": time.monotonic() - self._start_time,
        }
