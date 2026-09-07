from contextlib import contextmanager

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_owned_knowledge_base
from app.core.config import get_settings
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.models.models import EvalQuestion, EvalRun, User
from app.schemas.schemas import EvalQuestionCreate, EvalRunRequest
from app.services.eval.evaluator import run_evaluation

router = APIRouter(prefix="/api/knowledge-bases/{kb_id}/eval", tags=["evaluation"])


@contextmanager
def _apply_config_overrides(config: dict):
    """Temporarily applies experiment config (chunk_size, hybrid on/off,
    reranker on/off) to the process-wide settings singleton for the duration
    of an eval run, then restores the originals. Lets Configuration A / B
    comparisons (spec section 28) actually exercise different pipeline
    behavior without duplicating the whole settings/pipeline stack."""
    settings = get_settings()
    original = {
        "RERANKER_ENABLED": settings.RERANKER_ENABLED,
        "HYBRID_KEYWORD_WEIGHT": settings.HYBRID_KEYWORD_WEIGHT,
        "HYBRID_VECTOR_WEIGHT": settings.HYBRID_VECTOR_WEIGHT,
    }
    try:
        if "reranker" in config:
            settings.RERANKER_ENABLED = bool(config["reranker"])
        if "hybrid" in config and not config["hybrid"]:
            # disable hybrid by zeroing the keyword weight -> effectively vector-only
            settings.HYBRID_KEYWORD_WEIGHT = 0.0
            settings.HYBRID_VECTOR_WEIGHT = 1.0
        yield
    finally:
        for key, value in original.items():
            setattr(settings, key, value)


@router.post("/questions")
def add_eval_question(kb_id: str, payload: EvalQuestionCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    get_owned_knowledge_base(kb_id, db, user)
    eq = EvalQuestion(
        knowledge_base_id=kb_id,
        question=payload.question,
        expected_answer=payload.expected_answer,
        expected_document=payload.expected_document,
        expected_page=payload.expected_page,
        is_answerable=payload.is_answerable,
    )
    db.add(eq)
    db.commit()
    db.refresh(eq)
    return eq


@router.get("/questions")
def list_eval_questions(kb_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    get_owned_knowledge_base(kb_id, db, user)
    return db.query(EvalQuestion).filter(EvalQuestion.knowledge_base_id == kb_id).all()


@router.delete("/questions/{question_id}")
def delete_eval_question(kb_id: str, question_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    get_owned_knowledge_base(kb_id, db, user)
    db.query(EvalQuestion).filter(EvalQuestion.id == question_id, EvalQuestion.knowledge_base_id == kb_id).delete()
    db.commit()
    return {"deleted": True}


@router.post("/run")
@limiter.limit("3/minute")
def run_eval(request: Request, kb_id: str, payload: EvalRunRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    get_owned_knowledge_base(kb_id, db, user)

    with _apply_config_overrides(payload.config):
        metrics = run_evaluation(db, kb_id, payload.config)

    run = EvalRun(
        knowledge_base_id=kb_id,
        config=payload.config,
        questions_tested=metrics["questions_tested"],
        retrieval_recall=metrics["retrieval_recall"],
        context_precision=metrics["context_precision"],
        answer_faithfulness=metrics["answer_faithfulness"],
        citation_accuracy=metrics["citation_accuracy"],
        answer_relevance=metrics["answer_relevance"],
        unanswerable_detection=metrics["unanswerable_detection"],
        avg_latency_ms=metrics["avg_latency_ms"],
        details=metrics["details"],
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


@router.get("/runs")
def list_eval_runs(kb_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    get_owned_knowledge_base(kb_id, db, user)
    return db.query(EvalRun).filter(EvalRun.knowledge_base_id == kb_id).order_by(EvalRun.created_at.desc()).all()


@router.get("/runs/{run_a_id}/compare/{run_b_id}")
def compare_runs(kb_id: str, run_a_id: str, run_b_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Experiment comparison (spec section 28): shows Configuration A vs B
    metrics side by side, computed from two previously executed eval runs."""
    get_owned_knowledge_base(kb_id, db, user)
    run_a = db.query(EvalRun).filter(EvalRun.id == run_a_id, EvalRun.knowledge_base_id == kb_id).first()
    run_b = db.query(EvalRun).filter(EvalRun.id == run_b_id, EvalRun.knowledge_base_id == kb_id).first()

    metric_fields = [
        "retrieval_recall",
        "context_precision",
        "answer_faithfulness",
        "citation_accuracy",
        "answer_relevance",
        "unanswerable_detection",
        "avg_latency_ms",
    ]
    return {
        "run_a": {"id": run_a.id, "config": run_a.config, **{f: getattr(run_a, f) for f in metric_fields}},
        "run_b": {"id": run_b.id, "config": run_b.config, **{f: getattr(run_b, f) for f in metric_fields}},
    }