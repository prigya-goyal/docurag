from google import genai
from google.genai import errors, types
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from app.services.embeddings.base import EmbeddingProvider

# 768 is Google's recommended balance of quality vs. storage/compute cost
# (see Matryoshka Representation Learning note in Gemini Embedding docs).
OUTPUT_DIMENSIONS = 768


def _is_rate_limit_error(exc: BaseException) -> bool:
    # Only retry on 429 (quota/rate limit) — a real auth or bad-request error
    # should fail immediately rather than silently retrying 4 times.
    return isinstance(exc, errors.ClientError) and getattr(exc, "code", None) == 429


_retry_on_rate_limit = retry(
    retry=retry_if_exception(_is_rate_limit_error),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    stop=stop_after_attempt(6),
    reraise=True,
)


class GeminiEmbeddingProvider(EmbeddingProvider):
    """Uses Gemini's hosted embedding API instead of a locally-loaded
    sentence-transformers model. No PyTorch/model weights loaded into the
    backend process — this matters on memory-constrained hosts (e.g. a
    512MB free-tier container), where loading sentence-transformers plus a
    cross-encoder reranker can exceed the available RAM and crash the
    service. Uses the asymmetric RETRIEVAL_DOCUMENT / RETRIEVAL_QUERY task
    types, which the model is specifically tuned for and meaningfully
    improves retrieval quality over treating queries and documents the same.

    The free tier caps embedding calls at a fairly low requests-per-minute
    limit, and a burst of activity (bulk document ingestion overlapping with
    live queries) can exceed it. Retries with exponential backoff on 429s
    rather than failing the whole document outright.
    """

    def __init__(self, api_key: str, model: str = "gemini-embedding-001"):
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required when EMBEDDING_PROVIDER=gemini")
        self.client = genai.Client(api_key=api_key)
        self.model = model

    @_retry_on_rate_limit
    def _embed_batch(self, texts: list[str], task_type: str) -> list[list[float]]:
        response = self.client.models.embed_content(
            model=self.model,
            contents=texts,
            config=types.EmbedContentConfig(
                task_type=task_type,
                output_dimensionality=OUTPUT_DIMENSIONS,
            ),
        )
        return [e.values for e in response.embeddings]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        out: list[list[float]] = []
        batch_size = 20  # keep request payloads modest
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            out.extend(self._embed_batch(batch, "RETRIEVAL_DOCUMENT"))
        return out

    def embed_query(self, text: str) -> list[float]:
        return self._embed_batch([text], "RETRIEVAL_QUERY")[0]

    @property
    def dimensions(self) -> int:
        return OUTPUT_DIMENSIONS