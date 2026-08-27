import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import (
    analytics,
    auth,
    chat,
    compare,
    dashboard,
    debug,
    documents,
    evaluation,
    feedback,
    knowledge_bases,
    questions,
    search,
    summarize,
)
from app.core.config import get_settings
from app.core.database import Base, engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

# Ensure storage directories exist before anything tries to write to them
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.VECTOR_DB_DIR).mkdir(parents=True, exist_ok=True)

# MVP schema management: create tables on startup. Swap for Alembic
# migrations before running this against a real production database.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="Universal document intelligence & RAG platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME}


app.include_router(auth.router)
app.include_router(knowledge_bases.router)
app.include_router(documents.router)
app.include_router(search.router)
app.include_router(chat.router)
app.include_router(compare.router)
app.include_router(summarize.router)
app.include_router(questions.router)
app.include_router(feedback.router)
app.include_router(dashboard.router)
app.include_router(analytics.router)
app.include_router(debug.router)
app.include_router(evaluation.router)
