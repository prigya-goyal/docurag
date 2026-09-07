"""
Lightweight in-process TTL cache.

Not Redis — deliberately simple, size-capped, in-memory. Good enough for a
single-instance deployment; swap for Redis if you scale to multiple backend
replicas (the interface here is small enough to reimplement against Redis
without touching call sites).

Caches three things per the spec's caching requirements:
  - Embeddings: identical text embedded twice (e.g. the same question asked
    by different users, or FAQ-style repeats) skips the model call entirely.
  - Repeated retrieval queries: identical (kb_id, query, filters) tuples
    within the TTL window skip hybrid retrieval + reranking.
  - Frequently asked questions: identical (kb_id, question) chat turns with
    no conversation history skip the LLM generation call too.
"""
from __future__ import annotations

import hashlib
import time
from collections import OrderedDict
from threading import Lock
from typing import Any


class TTLCache:
    def __init__(self, max_size: int = 500, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._store: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._lock = Lock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if time.time() > expires_at:
                del self._store[key]
                return None
            # LRU touch
            self._store.move_to_end(key)
            return value

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._store[key] = (time.time() + self.ttl_seconds, value)
            self._store.move_to_end(key)
            while len(self._store) > self.max_size:
                self._store.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


def make_key(*parts: str) -> str:
    joined = "||".join(parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


# Module-level singletons. Never cache anything containing document text that
# should be invalidated on document delete — these are deliberately scoped to
# short-lived, read-heavy data (embeddings of query strings, retrieval
# results, full FAQ-style answers) where slightly-stale results within the
# TTL window are an acceptable, explicit tradeoff for the free tier.
embedding_cache = TTLCache(max_size=2000, ttl_seconds=24 * 3600)
retrieval_cache = TTLCache(max_size=500, ttl_seconds=10 * 60)
faq_cache = TTLCache(max_size=500, ttl_seconds=30 * 60)