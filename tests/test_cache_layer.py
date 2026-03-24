"""Tests for CacheLayer and CacheResult — 9 tests."""

import pytest
from agent_cache import ExactCache, SemanticCache, CacheLayer, CacheResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_layer(exact_size=100, semantic_threshold=0.85):
    exact = ExactCache(max_size=exact_size, ttl_seconds=3600)
    semantic = SemanticCache(threshold=semantic_threshold, max_size=50, ttl_seconds=7200)
    return CacheLayer(exact, semantic)


# ---------------------------------------------------------------------------
# Test 1: exact hit returns CacheResult with cache_type="exact"
# ---------------------------------------------------------------------------
def test_layer_exact_hit():
    layer = make_layer()
    layer.set("What is Python?", "A programming language.")
    result = layer.get("What is Python?")
    assert result is not None
    assert isinstance(result, CacheResult)
    assert result.cache_type == "exact"
    assert result.response == "A programming language."
    assert result.similarity is None
    assert result.age_seconds >= 0


# ---------------------------------------------------------------------------
# Test 2: complete miss returns None
# ---------------------------------------------------------------------------
def test_layer_miss():
    layer = make_layer()
    result = layer.get("totally unknown prompt xyz")
    assert result is None


# ---------------------------------------------------------------------------
# Test 3: semantic hit after distinct (non-exact) prompt
# ---------------------------------------------------------------------------
def test_layer_semantic_hit():
    layer = make_layer(semantic_threshold=0.4)
    layer.set("explain neural networks to me", "Neural networks explanation")
    # Different wording but semantically similar
    result = layer.get("can you explain neural networks")
    assert result is not None
    assert result.cache_type == "semantic"
    assert result.similarity is not None
    assert 0.0 < result.similarity <= 1.0


# ---------------------------------------------------------------------------
# Test 4: wrap decorator caches transparently
# ---------------------------------------------------------------------------
def test_layer_wrap_decorator():
    layer = make_layer()
    call_count = 0

    @layer.wrap
    def mock_llm(prompt: str) -> str:
        nonlocal call_count
        call_count += 1
        return f"Response to: {prompt}"

    # First call — should invoke the real function
    r1 = mock_llm("hello world")
    assert call_count == 1
    assert r1 == "Response to: hello world"

    # Second call with same prompt — should be cached (no extra call)
    r2 = mock_llm("hello world")
    assert call_count == 1  # NOT incremented
    assert r2 == r1


# ---------------------------------------------------------------------------
# Test 5: stats tracks exact_hits, semantic_hits, misses, total_saved_calls
# ---------------------------------------------------------------------------
def test_layer_stats():
    layer = make_layer()
    layer.set("prompt one", "resp one")
    layer.get("prompt one")       # exact hit
    layer.get("unknown prompt")   # miss

    s = layer.stats()
    assert s["exact_hits"] == 1
    assert s["misses"] == 1
    assert s["total_saved_calls"] == 1
    assert s["total_calls"] == 2
    assert abs(s["overall_hit_rate"] - 0.5) < 1e-9


# ---------------------------------------------------------------------------
# Test 6: CacheResult validates cache_type
# ---------------------------------------------------------------------------
def test_cache_result_invalid_type():
    with pytest.raises(ValueError):
        CacheResult(response="x", cache_type="invalid")


# ---------------------------------------------------------------------------
# Test 7: CacheResult validates similarity range
# ---------------------------------------------------------------------------
def test_cache_result_invalid_similarity():
    with pytest.raises(ValueError):
        CacheResult(response="x", cache_type="semantic", similarity=1.5)
    with pytest.raises(ValueError):
        CacheResult(response="x", cache_type="semantic", similarity=-0.1)


# ---------------------------------------------------------------------------
# Test 8: CacheResult validates age_seconds
# ---------------------------------------------------------------------------
def test_cache_result_invalid_age():
    with pytest.raises(ValueError):
        CacheResult(response="x", cache_type="exact", age_seconds=-1.0)


# ---------------------------------------------------------------------------
# Test 9: exact match takes priority over semantic
# ---------------------------------------------------------------------------
def test_layer_exact_beats_semantic():
    layer = make_layer(semantic_threshold=0.1)  # very low threshold
    layer.set("Python programming language", "Exact response")
    # Exact match should be returned, not semantic
    result = layer.get("Python programming language")
    assert result is not None
    assert result.cache_type == "exact"
