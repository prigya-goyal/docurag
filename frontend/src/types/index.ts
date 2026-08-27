export interface User {
  id: string;
  email: string;
  full_name: string;
  created_at: string;
}

export interface KnowledgeBase {
  id: string;
  name: string;
  description: string;
  document_count: number;
  created_at: string;
  updated_at: string;
}

export type ProcessingStatus =
  | "UPLOADING"
  | "PROCESSING"
  | "OCR"
  | "CHUNKING"
  | "EMBEDDING"
  | "INDEXING"
  | "COMPLETED"
  | "FAILED";

export interface DocumentItem {
  id: string;
  knowledge_base_id: string;
  filename: string;
  file_type: string;
  file_size_bytes: number;
  status: ProcessingStatus;
  status_detail: string;
  progress_pct: number;
  page_count: number;
  chunk_count: number;
  used_ocr: boolean;
  processing_time_ms: number;
  created_at: string;
}

export interface Citation {
  document_id: string;
  filename: string;
  page_number: number;
  section: string;
  chunk_id: string;
  snippet: string;
  relevance_score: number;
}

export interface RetrievedCandidateDebug {
  document_id: string;
  filename: string;
  chunk_id: string;
  page_number: number;
  vector_score: number;
  bm25_score: number;
  hybrid_score: number;
  reranker_score: number | null;
  used_in_context: boolean;
}

export interface ChatResponse {
  conversation_id: string;
  message_id: string;
  answer: string;
  rewritten_query: string;
  citations: Citation[];
  grounding_label: "HIGH" | "MEDIUM" | "LOW";
  grounding_score: number;
  source_count: number;
  retrieved_chunks: number;
  retrieval_debug: RetrievedCandidateDebug[];
  latency_ms: Record<string, number>;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: Citation[];
  grounding_label: string;
  grounding_score: number;
  created_at: string;
}

export interface Conversation {
  id: string;
  knowledge_base_id: string;
  title: string;
  updated_at: string;
}

export interface DashboardSummary {
  knowledge_bases: number;
  documents: number;
  pages: number;
  indexed_chunks: number;
  questions_asked: number;
  average_retrieval_score: number;
  recent_documents: { id: string; filename: string; status: string }[];
  recent_conversations: { id: string; title: string; updated_at: string }[];
  processing_status: Record<string, number>;
}
