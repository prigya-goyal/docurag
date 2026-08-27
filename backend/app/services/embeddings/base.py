from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """Common interface so the embedding backend can be swapped via env vars
    without touching ingestion, retrieval, or any other application code."""

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        ...

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        ...

    @property
    @abstractmethod
    def dimensions(self) -> int:
        ...
