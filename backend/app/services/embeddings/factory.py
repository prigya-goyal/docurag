from functools import lru_cache

from app.core.config import get_settings
from app.services.embeddings.base import EmbeddingProvider


@lru_cache
def get_embedding_provider() -> EmbeddingProvider:
    settings = get_settings()

    if settings.EMBEDDING_PROVIDER == "openai":
        from app.services.embeddings.openai_provider import OpenAIEmbeddingProvider

        return OpenAIEmbeddingProvider(api_key=settings.OPENAI_API_KEY, model=settings.OPENAI_EMBEDDING_MODEL)

    # default: local, no API key needed
    from app.services.embeddings.local_provider import get_local_provider

    return get_local_provider(settings.EMBEDDING_MODEL)
