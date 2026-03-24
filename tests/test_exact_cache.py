"""Tests for ExactCache — 10 tests."""

import time
import pytest
from agent_cache import ExactCache


# ---------------------------------------------------------------------------
# Test 1: basic set/get round-trip
# ---------------------------------------------------------------------------
def test_exact_basic_set_get():
    cache = ExactCache()
    cache.set("What is Python?", "Python is a language.")
    result = cache.get("What is Python?")
    assert result == "Python is a language."


# ---------------------------------------------------------------------------
# Test 2: cache miss returns None
# ---------------------------------------------------------------------------
def test_exact_cache_miss():
    cache = ExactCache()
    result = cache.get("unknown prompt")
    assert result is None


# ---------------------------------------------------------------------------
# Test 3: prompts are case-sensitive (different hashes)
# ---------------------------------------------------------------------------
def test_exact_case_sensitivity():
    cache = ExactCache()
    cache.set("hello", "lower")
    assert cache.get("Hello") is None
    assert cache.get("hello") == "lower"


# ---------------------------------------------------------------------------
# Test 4: TTL expiry
# ---------------------------------------------------------------------------
def test_exact_ttl_expiry():
    cache = ExactCache(ttl_seconds=1)
    cache.set("expiring prompt", "response")
    assert cache.get("expiring prompt") == "response"
    time.sleep(1.05)
    assert cache.get("expiring prompt") is None


# ---------------------------------------------------------------------------
# Test 5: LRU eviction when max_size exceeded
# ---------------------------------------------------------------------------
def test_exact_lru_eviction():
    cache = ExactCache(max_size=3)
    cache.set("a", "1")
    cache.set("b", "2")
    cache.set("c", "3")
    # Access 'a' to make it recently used
    cache.get("a")
    # Adding 'd' should evict 'b' (oldest unused)
    cache.set("d", "4")
    assert cache.get("a") == "1"
    assert cache.get("b") is None  # evicted
    assert cache.get("c") == "3"
    assert cache.get("d") == "4"


# ---------------------------------------------------------------------------
# Test 6: invalidate removes entry
# ---------------------------------------------------------------------------
def test_exact_invalidate():
    cache = ExactCache()
    cache.set("to delete", "gone")
    assert cache.get("to delete") == "gone"
    removed = cache.invalidate("to delete")
    assert removed is True
    assert cache.get("to delete") is None


# ---------------------------------------------------------------------------
# Test 7: invalidate non-existent returns False
# ---------------------------------------------------------------------------
def test_exact_invalidate_missing():
    cache = ExactCache()
    assert cache.invalidate("ghost") is False


# ---------------------------------------------------------------------------
# Test 8: clear empties all entries
# ---------------------------------------------------------------------------
def test_exact_clear():
    cache = ExactCache()
    for i in range(10):
        cache.set(f"prompt {i}", f"resp {i}")
    cache.clear()
    for i in range(10):
        assert cache.get(f"prompt {i}") is None


# ---------------------------------------------------------------------------
# Test 9: stats accuracy — hits, misses, hit_rate, size, evictions
# ---------------------------------------------------------------------------
def test_exact_stats():
    cache = ExactCache(max_size=2)
    cache.set("p1", "r1")
    cache.set("p2", "r2")
    cache.get("p1")   # hit
    cache.get("p1")   # hit
    cache.get("no")   # miss
    cache.set("p3", "r3")  # evicts p2 (LRU)

    s = cache.stats()
    assert s["hits"] == 2
    assert s["misses"] == 1
    assert abs(s["hit_rate"] - 2 / 3) < 1e-9
    assert s["evictions"] >= 1


# ---------------------------------------------------------------------------
# Test 10: invalid constructor args raise ValueError
# ---------------------------------------------------------------------------
def test_exact_invalid_args():
    with pytest.raises(ValueError):
        ExactCache(max_size=0)
    with pytest.raises(ValueError):
        ExactCache(ttl_seconds=-1)
