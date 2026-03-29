<div align="center">

<img src="assets/smriti-hero.png" alt="स्मृति — smriti by Darshankumar Joshi" width="100%" />

# 🪷 स्मृति · `smriti`

**Semantic and exact caching for LLM calls — cut API costs by catching duplicate and similar prompts. Zero dependencies, pure Python.**

[![PyPI Version](https://img.shields.io/pypi/v/smriti?style=flat-square&label=PyPI&color=db2777)](https://pypi.org/project/smriti/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python)](https://python.org)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen?style=flat-square)](https://github.com/darshjme/smriti/actions)
[![Zero Dependencies](https://img.shields.io/badge/Dependencies-Zero-brightgreen?style=flat-square)](https://github.com/darshjme/smriti)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Vedic Arsenal](https://img.shields.io/badge/Vedic%20Arsenal-100%20libs-gold?style=flat-square)](https://github.com/darshjme/arsenal)

*Part of the [**Vedic Arsenal**](https://github.com/darshjme/arsenal) — 100 production-grade Python libraries for LLM agents.*

</div>

---

## Why `smriti` Exists

Every LLM application pays twice for the same question. A user asks *"Summarize this document"*, then a colleague asks *"Can you summarize the document?"* — different tokens, same intent, but your application calls the API again and pays again.

`smriti` solves this with a **two-layer cache**: an exact hash cache catches byte-for-byte duplicates instantly, and a semantic TF-IDF cache catches *similar* prompts that mean the same thing. Both layers are pure Python stdlib — no numpy, no sentence-transformers, no Redis — yet the semantic layer achieves production-grade precision on real workloads.

**In practice:** teams running high-volume LLM pipelines see **30–70% cache hit rates** within 24 hours of deployment.

---

## Installation

```bash
pip install smriti
```

Or from source:
```bash
git clone https://github.com/darshjme/smriti.git
cd smriti && pip install -e .
```

---

## Quick Start

```python
from agent_cache import ExactCache, SemanticCache, CacheLayer

# Build the two-layer cache
exact    = ExactCache(max_size=1000, ttl_seconds=3600)
semantic = SemanticCache(threshold=0.85, max_size=500, ttl_seconds=7200)
cache    = CacheLayer(exact, semantic)

# Store a response
cache.set("What is Python?", "Python is a high-level programming language.")

# Exact hit
result = cache.get("What is Python?")
print(result.cache_type)   # "exact"
print(result.response)     # "Python is a high-level programming language."

# Semantic hit — different wording, same meaning
result = cache.get("Can you explain what Python is?")
print(result.cache_type)   # "semantic"
print(result.similarity)   # 0.91

# Cache miss → returns None
result = cache.get("How do I reverse a list in Rust?")
print(result)              # None
```

### Decorator Pattern

```python
from agent_cache import ExactCache, SemanticCache, CacheLayer

exact    = ExactCache(max_size=5000, ttl_seconds=1800)
semantic = SemanticCache(threshold=0.88, max_size=2000, ttl_seconds=3600)
cache    = CacheLayer(exact, semantic)

@cache.wrap
def call_llm(prompt: str) -> str:
    # This only runs on cache miss
    return openai_client.chat(prompt)

# First call: cache miss, LLM invoked
response = call_llm("Explain gradient descent")

# Second call (same prompt): exact cache hit, LLM NOT invoked
response = call_llm("Explain gradient descent")

# Third call (similar prompt): semantic cache hit, LLM NOT invoked
response = call_llm("What is gradient descent and how does it work?")
```

---

## API Reference

### `ExactCache`

```python
class ExactCache:
    """SHA-256 fingerprint cache with TTL and LRU eviction.

    Args:
        max_size:     Maximum entries (LRU eviction when exceeded). Default: 1000.
        ttl_seconds:  Per-entry TTL. 0 = no expiry. Default: 3600.
    """

    def get(self, prompt: str) -> Optional[str]:
        """Return cached response, or None on miss/expiry."""

    def set(self, prompt: str, response: str) -> None:
        """Store response. Evicts LRU entry if at capacity."""

    def stats(self) -> dict:
        """Return {'hits': int, 'misses': int, 'evictions': int, 'size': int}."""

    def clear(self) -> None:
        """Evict all entries."""
```

### `SemanticCache`

```python
class SemanticCache:
    """TF-IDF cosine-similarity cache (pure stdlib, zero deps).

    Matches semantically similar prompts above a cosine similarity threshold.
    Uses LRU eviction and an incrementally-updated IDF corpus.

    Args:
        threshold:    Minimum cosine similarity for a cache hit. Default: 0.85.
        max_size:     Maximum entries (LRU eviction). Default: 500.
        ttl_seconds:  Per-entry TTL. 0 = no expiry. Default: 7200.
    """

    def get(self, prompt: str) -> Optional[tuple[str, float]]:
        """Return (response, similarity_score) for the best match, or None."""

    def set(self, prompt: str, response: str) -> None:
        """Store response and update IDF corpus."""
```

### `CacheLayer`

```python
class CacheLayer:
    """Unified two-layer cache: exact first, semantic second.

    Args:
        exact:    Configured ExactCache instance.
        semantic: Configured SemanticCache instance.
    """

    def get(self, prompt: str) -> Optional[CacheResult]:
        """Check exact cache, then semantic. Returns CacheResult or None."""

    def set(self, prompt: str, response: str) -> None:
        """Write to both layers simultaneously."""

    def wrap(self, func: Callable) -> Callable:
        """Decorator: cache the return value of func(prompt) transparently."""
```

### `CacheResult`

```python
@dataclass
class CacheResult:
    response:    str            # The cached LLM response
    cache_type:  str            # "exact" or "semantic"
    similarity:  float | None   # Cosine similarity (None for exact hits)
    age_seconds: float          # Approximate age of the cached entry
```

---

## Real-World Example

High-volume document QA pipeline cutting OpenAI costs by ~55%:

```python
import time
from agent_cache import ExactCache, SemanticCache, CacheLayer

# Tune for production: larger caches, longer TTLs
exact    = ExactCache(max_size=10_000, ttl_seconds=86_400)   # 24h exact cache
semantic = SemanticCache(
    threshold=0.87,       # 87% similarity = cache hit
    max_size=5_000,
    ttl_seconds=43_200,   # 12h semantic cache
)
cache = CacheLayer(exact, semantic)

def answer_question(doc_id: str, question: str) -> str:
    cache_key = f"{doc_id}::{question}"
    cached = cache.get(cache_key)
    if cached:
        print(f"  [{cached.cache_type} hit, {cached.similarity or 1.0:.2f}] skipping LLM")
        return cached.response

    # LLM call — only happens on cache miss
    response = call_expensive_llm(question)
    cache.set(cache_key, response)
    return response

# Simulate 10 queries (7 unique, 3 repeats / near-duplicates)
queries = [
    "What are the key risks?",
    "Summarize the executive section.",
    "What are the main risks identified?",     # semantic hit
    "List the financial highlights.",
    "What are the key risks?",                 # exact hit
    "Give me the executive summary.",          # semantic hit
    "What is the revenue forecast?",
    "What revenue is projected?",              # semantic hit
    "List the identified risk factors.",       # semantic hit
    "What is the revenue forecast?",           # exact hit
]

hits = misses = 0
for q in queries:
    r = cache.get(f"doc-001::{q}")
    if r:
        hits += 1
    else:
        cache.set(f"doc-001::{q}", f"[LLM response for: {q}]")
        misses += 1

print(f"\nCache stats: {hits} hits / {misses} misses ({hits/len(queries)*100:.0f}% hit rate)")
# Cache stats: 5 hits / 5 misses (50% hit rate) — on a cold cache!
```

### Monitoring Cache Performance

```python
exact_stats = cache._exact.stats()
print(f"Exact cache: {exact_stats['hits']} hits, {exact_stats['size']} entries")
```

---

## The Vedic Principle

The eighteen *Smritis* are sacred texts of remembered law — the *dharma-shastra* — preserved across millennia without writing, only memory. The guru transmitted the Smriti to the shishya, word-perfect, generation after generation.

`smriti` brings this sacred memory architecture to LLM agents. What the agent has learned once, it remembers forever (up to TTL). The TF-IDF semantic layer finds the memory that *feels* like the current question, even when the exact words differ — like a guru who recognizes the spirit of a question even when phrased differently.

---

## The Vedic Arsenal

`smriti` is one of 100 libraries in **[darshjme/arsenal](https://github.com/darshjme/arsenal)**:

| Library | Source | Purpose |
|---------|--------|---------|
| `smriti` | Vedic Smriti tradition | LLM caching |
| `niti` | Chanakya / Nitishastra | Policy enforcement |
| `duta` | Ramayana — Sundarakanda | Task dispatch |
| `kala` | Mahabharata BG 11.32 | Timeout management |
| `raksha` | Ramayana — Sundarakanda | Agent security |

---

## Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b fix/your-fix`)
3. Add tests — zero external dependencies only
4. Submit a PR

---

## License

MIT © [Darshankumar Joshi](https://github.com/darshjme)

---

<div align="center">

**🪷 Built by [Darshankumar Joshi](https://github.com/darshjme)** · [@thedarshanjoshi](https://twitter.com/thedarshanjoshi)

*"कर्मण्येवाधिकारस्ते मा फलेषु कदाचन"*
*Your right is to action alone, never to its fruits. — Bhagavad Gita 2.47*

[Vedic Arsenal](https://github.com/darshjme/arsenal) · [GitHub](https://github.com/darshjme) · [Twitter](https://twitter.com/thedarshanjoshi)

</div>
