from functools import lru_cache

from app.core.cache import embedding_cache, make_key
from app.core.config import get_settings
from app.services.embeddings.base import EmbeddingProvider


class CachingEmbeddingProvider(EmbeddingProvider):
    """Wraps a real provider and caches query embeddings (the ones that
    repeat often — the same or similar questions asked across users/sessions)
    so identical queries skip the model call entirely. Document embeddings
    during ingestion are NOT cached here since each chunk is normally unique
    and caching them would just waste memory."""

    def __init__(self, inner: EmbeddingProvider):
        self._inner = inner

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._inner.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        key = make_key("embed_query", self._inner.__class__.__name__, text)
        cached = embedding_cache.get(key)
        if cached is not None:
            return cached
        result = self._inner.embed_query(text)
        embedding_cache.set(key, result)
        return result

    @property
    def dimensions(self) -> int:
        return self._inner.dimensions


@lru_cache
def get_embedding_provider() -> EmbeddingProvider:
    settings = get_settings()

    if settings.EMBEDDING_PROVIDER == "openai":
        from app.services.embeddings.openai_provider import OpenAIEmbeddingProvider

        inner = OpenAIEmbeddingProvider(api_key=settings.OPENAI_API_KEY, model=settings.OPENAI_EMBEDDING_MODEL)
    else:
        # default: local, no API key needed
        from app.services.embeddings.local_provider import get_local_provider

        inner = get_local_provider(settings.EMBEDDING_MODEL)

    return CachingEmbeddingProvider(inner)