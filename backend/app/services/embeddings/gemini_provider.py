from google import genai
from google.genai import types

from app.services.embeddings.base import EmbeddingProvider

# 768 is Google's recommended balance of quality vs. storage/compute cost
# (see Matryoshka Representation Learning note in Gemini Embedding docs).
OUTPUT_DIMENSIONS = 768


class GeminiEmbeddingProvider(EmbeddingProvider):
    """Uses Gemini's hosted embedding API instead of a locally-loaded
    sentence-transformers model. No PyTorch/model weights loaded into the
    backend process — this matters on memory-constrained hosts (e.g. a
    512MB free-tier container), where loading sentence-transformers plus a
    cross-encoder reranker can exceed the available RAM and crash the
    service. Uses the asymmetric RETRIEVAL_DOCUMENT / RETRIEVAL_QUERY task
    types, which the model is specifically tuned for and meaningfully
    improves retrieval quality over treating queries and documents the same.
    """

    def __init__(self, api_key: str, model: str = "gemini-embedding-001"):
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required when EMBEDDING_PROVIDER=gemini")
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        out: list[list[float]] = []
        batch_size = 20  # keep request payloads modest
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            response = self.client.models.embed_content(
                model=self.model,
                contents=batch,
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT",
                    output_dimensionality=OUTPUT_DIMENSIONS,
                ),
            )
            out.extend([e.values for e in response.embeddings])
        return out

    def embed_query(self, text: str) -> list[float]:
        response = self.client.models.embed_content(
            model=self.model,
            contents=[text],
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY",
                output_dimensionality=OUTPUT_DIMENSIONS,
            ),
        )
        return response.embeddings[0].values

    @property
    def dimensions(self) -> int:
        return OUTPUT_DIMENSIONS