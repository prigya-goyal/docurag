"""
Central application configuration.

Everything that could vary between environments (secrets, model providers,
chunking parameters, retrieval weights) is read from environment variables
so the application never hard-codes API keys or provider choices.
"""
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Core app ---
    APP_NAME: str = "DocuRAG"
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    ALGORITHM: str = "HS256"

    # --- Database ---
    # SQLite by default so the project runs with zero external services;
    # point this at Postgres in docker-compose / production.
    DATABASE_URL: str = "sqlite:///./docurag.db"

    # --- Storage ---
    UPLOAD_DIR: str = "./storage/uploads"
    VECTOR_DB_DIR: str = "./storage/vectordb"
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: tuple[str, ...] = (".pdf", ".docx", ".pptx", ".txt", ".md", ".csv")

    # --- Embeddings (pluggable provider) ---
    EMBEDDING_PROVIDER: Literal["local", "openai", "gemini"] = "local"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    OPENAI_API_KEY: str | None = None
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"

    # --- Reranker ---
    RERANKER_ENABLED: bool = True
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # --- LLM (pluggable provider) ---
    LLM_PROVIDER: Literal["anthropic", "openai", "gemini"] = "anthropic"
    ANTHROPIC_API_KEY: str | None = None
    ANTHROPIC_MODEL: str = "claude-sonnet-4-6"
    OPENAI_LLM_MODEL: str = "gpt-4o-mini"
    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # --- Chunking ---
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 120
    MAX_CONTEXT_CHUNKS: int = 8

    # --- Hybrid retrieval ---
    RETRIEVAL_CANDIDATES: int = 25          # candidates pulled from each retriever pre-rerank
    RERANK_TOP_K: int = 6                   # chunks kept after reranking, sent to LLM
    HYBRID_VECTOR_WEIGHT: float = 0.6
    HYBRID_KEYWORD_WEIGHT: float = 0.4

    # --- Grounding / safety thresholds ---
    MIN_GROUNDING_SCORE: float = 0.35       # below this -> "not found"

    # --- CORS ---
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
