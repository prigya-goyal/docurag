from functools import lru_cache

from app.services.embeddings.base import EmbeddingProvider


class LocalEmbeddingProvider(EmbeddingProvider):
    """Runs a sentence-transformers model locally. Default provider so the
    project works out of the box with no external API key."""

    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer  # imported lazily: heavy dependency

        self.model_name = model_name
        self._model = SentenceTransformer(model_name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._model.encode(texts, batch_size=32, show_progress_bar=False, normalize_embeddings=True).tolist()

    def embed_query(self, text: str) -> list[float]:
        return self._model.encode([text], normalize_embeddings=True)[0].tolist()

    @property
    def dimensions(self) -> int:
        return self._model.get_sentence_embedding_dimension()


@lru_cache
def get_local_provider(model_name: str) -> LocalEmbeddingProvider:
    # Cached so the (relatively expensive) model load happens once per process.
    return LocalEmbeddingProvider(model_name)
