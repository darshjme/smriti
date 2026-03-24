# agent-cache

**Semantic and exact caching for LLM calls — cut costs by catching duplicate and similar prompts.**

[![Python ≥ 3.10](https://img.shields.io/badge/python-%3E%3D3.10-blue)](https://www.python.org/)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## The Problem

Every LLM call costs money. Real-world agent workloads are full of:

- **Identical prompts** re-sent by different users or retry loops.
- **Semantically identical questions** phrased slightly differently.

Without a caching layer, you pay for every single one.

---

## The Solution

`agent-cache` intercepts LLM calls at two levels:

| Level | Method | Latency | When it fires |
|-------|--------|---------|---------------|
| **ExactCache** | SHA-256 hash lookup | O(1) | Byte-for-byte identical prompt |
| **SemanticCache** | TF-IDF cosine similarity | O(n) | Paraphrased / similar prompt |

Both caches support **TTL expiry** and **LRU eviction**. Zero runtime dependencies — pure Python stdlib only.

---

## Install

```bash
pip install agent-cache
```

---

## Quick Start

```python
from agent_cache import ExactCache, SemanticCache, CacheLayer

# Configure caches
exact    = ExactCache(max_size=1000, ttl_seconds=3600)
semantic = SemanticCache(threshold=0.85, max_size=500, ttl_seconds=7200)
cache    = CacheLayer(exact, semantic)

# Wrap your LLM function — caching is transparent
@cache.wrap
def call_llm(prompt: str) -> str:
    # Your actual API call here
    return expensive_openai_call(prompt)

# First call — hits the API
r1 = call_llm("What is machine learning?")

# Second call — served from ExactCache (free!)
r2 = call_llm("What is machine learning?")

# Paraphrased call — served from SemanticCache if similarity ≥ 0.85
r3 = call_llm("Can you explain machine learning to me?")

# Check savings
print(cache.stats())
# {
#   'exact_hits': 1,
#   'semantic_hits': 1,
#   'misses': 1,
#   'total_saved_calls': 2,
#   'total_calls': 3,
#   'overall_hit_rate': 0.667,
#   ...
# }
```

---

## Cost Savings Example

Assume your agent makes **10,000 LLM calls/day** at **$0.002/call** ($20/day):

| Cache Hit Rate | Calls Saved | Daily Saving | Monthly Saving |
|---------------|-------------|-------------|----------------|
| 10%           | 1,000       | $2.00       | $60            |
| **30%**       | **3,000**   | **$6.00**   | **$180**       |
| 50%           | 5,000       | $10.00      | $300           |
| 70%           | 7,000       | $14.00      | $420           |

> **30% cache hit rate = 30% cost reduction. No code changes needed — just wrap your LLM function.**

---

## API Reference

### ExactCache

```python
from agent_cache import ExactCache

cache = ExactCache(max_size=1000, ttl_seconds=3600)

cache.set("prompt", "response")          # Store
cache.get("prompt")                      # -> "response" | None
cache.invalidate("prompt")               # -> True if existed
cache.clear()                            # Wipe all
cache.stats()
# -> {"hits": 5, "misses": 2, "hit_rate": 0.71, "size": 42, "evictions": 0}
```

### SemanticCache

```python
from agent_cache import SemanticCache

cache = SemanticCache(threshold=0.85, max_size=500, ttl_seconds=7200)

cache.set("explain machine learning", "ML is...")
cache.get("what is machine learning?")           # -> ("ML is...", 0.91) | None
cache.find_similar("deep learning", top_k=3)     # -> [("explain machine learning", 0.88), ...]
cache.stats()
# -> {"hits": 3, "misses": 1, "hit_rate": 0.75, "avg_similarity": 0.91, "size": 10}
```

### CacheLayer

```python
from agent_cache import ExactCache, SemanticCache, CacheLayer, CacheResult

cache = CacheLayer(ExactCache(), SemanticCache())

# Manual
cache.set("prompt", "response")
result: CacheResult | None = cache.get("prompt")
if result:
    print(result.response)     # "response"
    print(result.cache_type)   # "exact" | "semantic"
    print(result.similarity)   # float | None
    print(result.age_seconds)  # float

# Decorator
@cache.wrap
def llm(prompt: str) -> str: ...

cache.stats()
# -> {"exact_hits": N, "semantic_hits": N, "misses": N, "total_saved_calls": N, ...}
```

### CacheResult

```python
from agent_cache import CacheResult

result = CacheResult(
    response="The answer is 42",
    cache_type="semantic",   # "exact" | "semantic"
    similarity=0.91,         # None for exact hits
    age_seconds=0.0001,
)
```

---

## How SemanticCache Works (No Magic)

1. **Tokenize** — lowercase, strip punctuation, split on word boundaries.
2. **TF-IDF** — weight tokens by term frequency × inverse document frequency over the cached corpus.
3. **Cosine similarity** — compare query vector against all stored vectors.
4. **Threshold** — return the best match only if it exceeds `threshold` (default 0.85).

All pure Python stdlib (`re`, `math`, `collections`). No numpy. No sentence-transformers. No vector DB.

---

## Configuration Guide

| Parameter | Default | Recommendation |
|-----------|---------|----------------|
| `ExactCache.ttl_seconds` | 3600 | Match your data freshness SLA |
| `ExactCache.max_size` | 1000 | Size to ~10% of daily unique prompts |
| `SemanticCache.threshold` | 0.85 | Lower (0.7) for broader matching; higher (0.95) for strict |
| `SemanticCache.ttl_seconds` | 7200 | Longer-lived — semantic matches age better |
| `SemanticCache.max_size` | 500 | Keep smaller; similarity search is O(n) |

---

## License

MIT
