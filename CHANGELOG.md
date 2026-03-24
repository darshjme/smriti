# Changelog

All notable changes to **agent-cache** are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/).

---

## [0.1.0] — 2024-03-24

### Added
- `ExactCache` — SHA-256 hash-based exact match cache with LRU eviction and TTL.
- `SemanticCache` — TF-IDF cosine-similarity cache (pure stdlib, zero dependencies).
- `CacheLayer` — unified interface combining both caches with priority ordering.
- `CacheResult` — typed dataclass with `response`, `cache_type`, `similarity`, `age_seconds`.
- `CacheLayer.wrap()` — transparent decorator for LLM function calls.
- Per-cache and combined statistics (`hits`, `misses`, `hit_rate`, `evictions`, `avg_similarity`).
- Full pytest test suite (22+ tests).

---

## [Unreleased]

### Planned
- Redis and SQLite persistence backends.
- Async-safe variants (`AsyncExactCache`, `AsyncSemanticCache`).
- Prometheus metrics export.
- CLI inspection tool (`agent-cache stats`).
