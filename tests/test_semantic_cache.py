"""Tests for SemanticCache — 8 tests."""

import time
import pytest
from agent_cache import SemanticCache


# ---------------------------------------------------------------------------
# Test 1: exact same text should hit with score ~1.0
# ---------------------------------------------------------------------------
def test_semantic_exact_text_hit():
    cache = SemanticCache(threshold=0.85)
    cache.set("machine learning algorithms", "ML algorithms response")
    result = cache.get("machine learning algorithms")
    assert result is not None
    response, score = result
    assert response == "ML algorithms response"
    assert score > 0.99


# ---------------------------------------------------------------------------
# Test 2: clearly unrelated prompt returns None
# ---------------------------------------------------------------------------
def test_semantic_unrelated_miss():
    cache = SemanticCache(threshold=0.85)
    cache.set("What is the capital of France?", "Paris")
    result = cache.get("How does photosynthesis work?")
    assert result is None


# ---------------------------------------------------------------------------
# Test 3: similar (paraphrased) prompt should hit above threshold
# ---------------------------------------------------------------------------
def test_semantic_similar_hit():
    cache = SemanticCache(threshold=0.4)
    cache.set("explain neural networks to me", "Neural networks are...")
    result = cache.get("can you explain neural networks")
    assert result is not None
    response, score = result
    assert response == "Neural networks are..."
    assert score >= 0.4


# ---------------------------------------------------------------------------
# Test 4: TTL expiry
# ---------------------------------------------------------------------------
def test_semantic_ttl_expiry():
    cache = SemanticCache(threshold=0.9, ttl_seconds=1)
    cache.set("expiring semantic prompt", "will expire")
    assert cache.get("expiring semantic prompt") is not None
    time.sleep(1.05)
    assert cache.get("expiring semantic prompt") is None


# ---------------------------------------------------------------------------
# Test 5: LRU eviction when max_size exceeded
# ---------------------------------------------------------------------------
def test_semantic_lru_eviction():
    cache = SemanticCache(threshold=0.99, max_size=2)
    cache.set("first entry abc", "resp1")
    cache.set("second entry def", "resp2")
    # This should evict oldest when adding third
    cache.set("third entry ghi", "resp3")
    assert cache.stats()["size"] == 2


# ---------------------------------------------------------------------------
# Test 6: find_similar returns top-k results
# ---------------------------------------------------------------------------
def test_semantic_find_similar():
    cache = SemanticCache(threshold=0.1)
    cache.set("deep learning basics", "DL basics")
    cache.set("deep learning advanced", "DL advanced")
    cache.set("cooking pasta recipe", "Recipe")
    similar = cache.find_similar("deep learning", top_k=2)
    assert len(similar) == 2
    # Top result should relate to "deep learning"
    assert "deep learning" in similar[0][0]
    # Scores should be descending
    assert similar[0][1] >= similar[1][1]


# ---------------------------------------------------------------------------
# Test 7: stats — hits, misses, avg_similarity, size
# ---------------------------------------------------------------------------
def test_semantic_stats():
    cache = SemanticCache(threshold=0.85)
    cache.set("python programming language", "Python info")
    cache.get("python programming language")  # hit
    cache.get("completely different topic xyz")  # miss
    s = cache.stats()
    assert s["hits"] == 1
    assert s["misses"] == 1
    assert s["avg_similarity"] > 0.0
    assert s["size"] == 1


# ---------------------------------------------------------------------------
# Test 8: invalid constructor args raise ValueError
# ---------------------------------------------------------------------------
def test_semantic_invalid_args():
    with pytest.raises(ValueError):
        SemanticCache(threshold=1.5)
    with pytest.raises(ValueError):
        SemanticCache(max_size=0)
    with pytest.raises(ValueError):
        SemanticCache(ttl_seconds=-5)
