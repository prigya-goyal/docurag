from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# ---------- Auth ----------
class UserRegister(BaseModel):
    email: EmailStr
    full_name: str
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Knowledge base ----------
class KnowledgeBaseCreate(BaseModel):
    name: str
    description: str = ""


class KnowledgeBaseUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class KnowledgeBaseOut(BaseModel):
    id: str
    name: str
    description: str
    document_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ---------- Documents ----------
class DocumentOut(BaseModel):
    id: str
    knowledge_base_id: str
    filename: str
    file_type: str
    file_size_bytes: int
    status: str
    status_detail: str
    progress_pct: int
    page_count: int
    chunk_count: int
    used_ocr: bool
    processing_time_ms: int
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Chat ----------
class ChatRequest(BaseModel):
    conversation_id: str | None = None
    knowledge_base_id: str
    message: str
    document_ids: list[str] | None = None  # optional metadata filter
    agentic: bool = False


class Citation(BaseModel):
    document_id: str
    filename: str
    page_number: int
    section: str = ""
    chunk_id: str
    snippet: str
    relevance_score: float


class RetrievedCandidateDebug(BaseModel):
    document_id: str
    filename: str
    chunk_id: str
    page_number: int
    vector_score: float
    bm25_score: float
    hybrid_score: float
    reranker_score: float | None = None
    used_in_context: bool


class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    answer: str
    rewritten_query: str
    citations: list[Citation]
    grounding_label: str
    grounding_score: float
    source_count: int
    retrieved_chunks: int
    retrieval_debug: list[RetrievedCandidateDebug]
    latency_ms: dict


class ConversationOut(BaseModel):
    id: str
    knowledge_base_id: str
    title: str
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    citations: list
    grounding_label: str
    grounding_score: float
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Feedback ----------
class FeedbackCreate(BaseModel):
    message_id: str
    feedback: str  # "up" | "down"
    reason: str | None = None  # incorrect_answer | wrong_source | missing_information | poor_explanation | hallucination


# ---------- Summarization / Question generation ----------
class SummarizeRequest(BaseModel):
    document_id: str
    mode: str = "executive"  # executive | tldr | key_points | explain_simply | section
    section: str | None = None


class QuestionGenRequest(BaseModel):
    document_id: str
    difficulty: str = "medium"  # easy | medium | hard
    count: int = 5


class CompareRequest(BaseModel):
    document_ids: list[str] = Field(min_length=2)
    focus: str | None = None  # e.g. "What changed?"


# ---------- Evaluation ----------
class EvalQuestionCreate(BaseModel):
    knowledge_base_id: str
    question: str
    expected_answer: str = ""
    expected_document: str = ""
    expected_page: int = 0
    is_answerable: bool = True


class EvalRunRequest(BaseModel):
    knowledge_base_id: str
    config: dict = Field(default_factory=dict)  # e.g. {"hybrid": true, "reranker": true, "chunk_size": 700}
