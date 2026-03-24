"""SemanticCache — TF-IDF cosine-similarity cache (pure stdlib, zero deps)."""

import math
import re
import time
from collections import Counter, OrderedDict
from typing import Optional


# ---------------------------------------------------------------------------
# Tiny TF-IDF engine (pure stdlib)
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> list[str]:
    """Lowercase, strip punctuation, split into tokens."""
    return re.findall(r"[a-z0-9]+", text.lower())


def _tf(tokens: list[str]) -> dict[str, float]:
    """Term frequency (raw count / total tokens)."""
    if not tokens:
        return {}
    counts = Counter(tokens)
    total = len(tokens)
    return {t: c / total for t, c in counts.items()}


def _build_vector(tokens: list[str], idf: dict[str, float]) -> dict[str, float]:
    """Multiply TF by IDF to get a TF-IDF weighted sparse vector."""
    tf = _tf(tokens)
    return {t: tf[t] * idf.get(t, 1.0) for t in tf}


def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    """Cosine similarity between two sparse vectors."""
    if not a or not b:
        return 0.0
    dot = sum(a[t] * b[t] for t in a if t in b)
    mag_a = math.sqrt(sum(v * v for v in a.values()))
    mag_b = math.sqrt(sum(v * v for v in b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


class SemanticCache:
    """Cosine-similarity cache using TF-IDF embeddings (pure stdlib).

    Finds semantically similar cached prompts above *threshold* without
    needing numpy, sentence-transformers, or any external vector DB.

    Args:
        threshold: Minimum cosine similarity to consider a cache hit (0-1).
        max_size: Maximum number of entries (LRU eviction).
        ttl_seconds: Entry TTL in seconds (0 = no expiry).
    """

    def __init__(
        self,
        threshold: float = 0.85,
        max_size: int = 500,
        ttl_seconds: int = 7200,
    ) -> None:
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("threshold must be between 0 and 1")
        if max_size < 1:
            raise ValueError("max_size must be >= 1")
        if ttl_seconds < 0:
            raise ValueError("ttl_seconds must be >= 0")

        self.threshold = threshold
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds

        # Ordered to support LRU eviction
        # key = original prompt str
        # value = (response, tokens, stored_at)
        self._store: OrderedDict[str, tuple[str, list[str], float]] = OrderedDict()

        # Corpus DF for IDF computation: token -> doc_count
        self._df: Counter[str] = Counter()

        self._hits = 0
        self._misses = 0
        self._similarity_sum = 0.0
        self._similarity_count = 0

    # ------------------------------------------------------------------
    # IDF
    # ------------------------------------------------------------------

    def _idf(self) -> dict[str, float]:
        """Compute IDF over the current corpus."""
        n = max(len(self._store), 1)
        return {
            t: math.log((n + 1) / (df + 1)) + 1.0
            for t, df in self._df.items()
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _is_expired(self, stored_at: float) -> bool:
        if self.ttl_seconds == 0:
            return False
        return (time.monotonic() - stored_at) > self.ttl_seconds

    def _evict_expired(self) -> None:
        expired = [
            k
            for k, (_, toks, ts) in list(self._store.items())
            if self._is_expired(ts)
        ]
        for k in expired:
            self._remove(k)

    def _remove(self, key: str) -> None:
        if key not in self._store:
            return
        _, tokens, _ = self._store.pop(key)
        unique_tokens = set(tokens)
        for t in unique_tokens:
            self._df[t] -= 1
            if self._df[t] <= 0:
                del self._df[t]

    def _add(self, prompt: str, response: str, tokens: list[str]) -> None:
        """Insert entry and update DF counters."""
        unique_tokens = set(tokens)
        for t in unique_tokens:
            self._df[t] += 1
        self._store[prompt] = (response, tokens, time.monotonic())
        # Evict LRU
        while len(self._store) > self.max_size:
            oldest_key = next(iter(self._store))
            self._remove(oldest_key)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, prompt: str) -> Optional[tuple[str, float]]:
        """Return (response, similarity_score) for the best match, or None."""
        self._evict_expired()
        if not self._store:
            self._misses += 1
            return None

        idf = self._idf()
        query_tokens = _tokenize(prompt)
        query_vec = _build_vector(query_tokens, idf)

        best_score = -1.0
        best_key: Optional[str] = None

        for key, (_, tokens, _) in self._store.items():
            vec = _build_vector(tokens, idf)
            score = _cosine(query_vec, vec)
            if score > best_score:
                best_score = score
                best_key = key

        if best_key is None or best_score < self.threshold:
            self._misses += 1
            return None

        response, _, stored_at = self._store[best_key]
        if self._is_expired(stored_at):
            self._remove(best_key)
            self._misses += 1
            return None

        # Move to end = most recently used
        self._store.move_to_end(best_key)
        self._hits += 1
        self._similarity_sum += best_score
        self._similarity_count += 1
        return response, best_score

    def set(self, prompt: str, response: str) -> None:
        """Store *response* keyed to *prompt*."""
        tokens = _tokenize(prompt)
        if not tokens:
            return  # skip empty prompts
        if prompt in self._store:
            self._remove(prompt)
        self._add(prompt, response, tokens)

    def find_similar(
        self, prompt: str, top_k: int = 3
    ) -> list[tuple[str, float]]:
        """Return top-k (prompt, similarity_score) pairs from the cache."""
        self._evict_expired()
        if not self._store:
            return []

        idf = self._idf()
        query_tokens = _tokenize(prompt)
        query_vec = _build_vector(query_tokens, idf)

        scored: list[tuple[str, float]] = []
        for key, (_, tokens, _) in self._store.items():
            vec = _build_vector(tokens, idf)
            score = _cosine(query_vec, vec)
            scored.append((key, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def stats(self) -> dict:
        """Return cache statistics."""
        self._evict_expired()
        total = self._hits + self._misses
        avg_sim = (
            self._similarity_sum / self._similarity_count
            if self._similarity_count
            else 0.0
        )
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self._hits / total if total else 0.0,
            "avg_similarity": avg_sim,
            "size": len(self._store),
        }
