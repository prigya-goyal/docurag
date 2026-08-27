# DocuRAG — Universal Document Intelligence & RAG Platform

Upload your knowledge. Ask questions. Get grounded answers.

DocuRAG is a full-stack RAG platform: document ingestion (with OCR fallback), structure-aware
chunking, hybrid vector + BM25 retrieval, cross-encoder reranking, conversational query rewriting,
grounded generation with real citations, hallucination/"not found" detection, document comparison,
hierarchical summarization, question generation, a retrieval debugger, and a RAG evaluation engine
that computes real metrics from actual pipeline runs.

## What's implemented vs. scaffolded

This was built and **tested end-to-end** (live HTTP calls against a running server, plus unit
tests of extraction/chunking/BM25/grounding logic) for:

- **Phase 1** — auth, knowledge bases, file upload, PDF/DOCX/PPTX/TXT/MD/CSV ingestion, chunking,
  embeddings, vector DB, basic RAG, citations.
- **Phase 2** — hybrid retrieval (vector + BM25), reranking, conversational RAG, query rewriting,
  source viewer, "not found" / grounding detection.
- **Phase 3** — document comparison, hierarchical map-reduce summarization, question generation,
  metadata filtering, feedback, analytics.
- **Phase 4** — evaluation framework (recall/precision/faithfulness/citation accuracy/relevance/
  unanswerable-detection, all computed from real runs), retrieval debugger, experiment A/B
  comparison.

**Phase 5 (optional, per the original spec's own phasing) is intentionally *not* implemented as
code** — knowledge graph extraction, multimodal (image/table) RAG, and the "keep it modular" caveat
around agentic retrieval. A minimal agentic retrieval mode (multi-query planning + synthesis) *is*
implemented (`app/services/rag/agentic.py`, toggled via the "Agentic" checkbox in the chat UI) as a
deliberately small example of the pattern, not a full implementation of Phase 5.

## Architecture

```
frontend (React + TypeScript + Tailwind)
        │  REST (JSON, JWT bearer auth)
        ▼
backend (FastAPI)
 ├── api/            route handlers, one file per resource
 ├── services/
 │    ├── ingestion/     extraction (PyMuPDF/docx/pptx/pandas), OCR (pytesseract), chunking
 │    ├── embeddings/    pluggable: local sentence-transformers (default) or OpenAI
 │    ├── vectorstore/   ChromaDB, filtered by knowledge_base_id / document_id
 │    ├── retrieval/     BM25, hybrid fusion, cross-encoder reranker, query rewriting
 │    ├── llm/           pluggable: Anthropic (default) or OpenAI
 │    ├── rag/           prompt construction (with prompt-injection defenses), grounding/
 │    │                  citation logic, the main pipeline orchestrator, agentic mode
 │    ├── processing/    background document processing pipeline
 │    └── eval/          evaluation engine (LLM-as-judge + heuristic metrics)
 └── models/         SQLAlchemy models (SQLite by default, Postgres-ready)
```

Every provider (embeddings, LLM, reranker on/off, vector DB) is swappable via environment
variables — see `backend/.env.example`. No API keys are hard-coded anywhere.

LLM provider options: **Anthropic** (default), **OpenAI**, or **Gemini**. Gemini's free tier
(no credit card, doesn't expire, ~1,500 requests/day on Flash models as of writing) is the
cheapest way to test this project end-to-end — get a key at https://aistudio.google.com/apikey
and set `LLM_PROVIDER=gemini` + `GEMINI_API_KEY=...` in `backend/.env`.

## Quick start (Docker)

```bash
cp backend/.env.example backend/.env
# edit backend/.env: set ANTHROPIC_API_KEY (or switch LLM_PROVIDER=openai + OPENAI_API_KEY)

docker compose up --build
```

- Frontend: http://localhost:5173
- Backend API docs: http://localhost:8000/docs

To use Postgres instead of the default SQLite:
```bash
docker compose --profile postgres up --build
# then set DATABASE_URL in backend/.env to the postgres:// URL shown in docker-compose.yml
```

## Quick start (local, no Docker)

**Backend:**
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit with your API key
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Note: `EMBEDDING_PROVIDER=local` (the default) downloads a small sentence-transformers model from
Hugging Face on first run, so the machine running the backend needs outbound internet access the
first time. Set `EMBEDDING_PROVIDER=openai` to avoid that if you'd rather use an API-based
embedding model throughout.

## Security notes

- Documents are treated as **untrusted data**, never instructions — see
  `backend/app/services/rag/prompts.py` and the adversarial test suite in
  `backend/app/services/rag/injection_tests.py` (`pytest app/services/rag/injection_tests.py`,
  requires a configured LLM key).
- JWT auth with per-user knowledge-base isolation enforced at the query level
  (`backend/app/api/deps.py::get_owned_knowledge_base`).
- File type and size are validated on upload; no client ever sees an API key — all provider calls
  happen server-side.

## Known limitations of this build

- Background processing uses FastAPI `BackgroundTasks` (in-process), which is fine for a
  single-instance deployment but won't survive a process restart mid-job or scale across multiple
  backend replicas. For that, swap in Celery + Redis (the pipeline function
  `services/processing/pipeline.py::process_document` is already a plain, side-effect-isolated
  function that drops into a Celery task unchanged).
- BM25 index is rebuilt from the relational `chunks` table on every query rather than cached — fine
  at demo scale, worth persisting/incrementally-updating at real scale.
- SQLite is the zero-setup default; switch to Postgres (`docker compose --profile postgres`) before
  any real concurrent-write load.
