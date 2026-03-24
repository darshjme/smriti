"""agent-cache: Semantic and exact caching for LLM calls."""

from .exact_cache import ExactCache
from .semantic_cache import SemanticCache
from .cache_layer import CacheLayer, CacheResult

__version__ = "0.1.0"
__all__ = ["ExactCache", "SemanticCache", "CacheLayer", "CacheResult"]
