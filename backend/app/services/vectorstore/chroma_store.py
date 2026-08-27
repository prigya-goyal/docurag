"""
Vector store layer, backed by ChromaDB (embedded, persisted to disk — no
separate server process required). Kept behind a narrow interface so a
different vector DB (Qdrant, Pinecone, pgvector, etc.) can be substituted
by implementing the same four methods.
"""
from __future__ import annotations

from functools import lru_cache

import chromadb

from app.core.config import get_settings

COLLECTION_NAME = "docurag_chunks"


class VectorStore:
    def __init__(self, persist_dir: str):
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
        )

    def upsert(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict],
    ) -> None:
        self.collection.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)

    def delete_by_document(self, document_id: str) -> None:
        self.collection.delete(where={"document_id": document_id})

    def delete_by_knowledge_base(self, knowledge_base_id: str) -> None:
        self.collection.delete(where={"knowledge_base_id": knowledge_base_id})

    def query(
        self,
        query_embedding: list[float],
        n_results: int,
        knowledge_base_id: str,
        document_ids: list[str] | None = None,
    ) -> list[dict]:
        where: dict = {"knowledge_base_id": knowledge_base_id}
        if document_ids:
            where = {"$and": [where, {"document_id": {"$in": document_ids}}]}

        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        if not result["ids"] or not result["ids"][0]:
            return []

        out = []
        for i, chunk_id in enumerate(result["ids"][0]):
            distance = result["distances"][0][i]
            # cosine distance -> similarity score in [0, 1]
            score = max(0.0, 1 - distance / 2)
            out.append(
                {
                    "chunk_id": chunk_id,
                    "text": result["documents"][0][i],
                    "metadata": result["metadatas"][0][i],
                    "vector_score": round(score, 4),
                }
            )
        return out


@lru_cache
def get_vector_store() -> VectorStore:
    settings = get_settings()
    return VectorStore(settings.VECTOR_DB_DIR)
