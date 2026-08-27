import { api } from "./client";
import type {
  ChatResponse,
  Conversation,
  DashboardSummary,
  DocumentItem,
  KnowledgeBase,
  Message,
  User,
} from "../types";

export const authApi = {
  register: (data: { email: string; full_name: string; password: string }) =>
    api.post<{ access_token: string; user: User }>("/api/auth/register", data),
  login: (data: { email: string; password: string }) =>
    api.post<{ access_token: string; user: User }>("/api/auth/login", data),
  me: () => api.get<User>("/api/auth/me"),
};

export const kbApi = {
  list: () => api.get<KnowledgeBase[]>("/api/knowledge-bases"),
  create: (data: { name: string; description?: string }) => api.post<KnowledgeBase>("/api/knowledge-bases", data),
  get: (id: string) => api.get<KnowledgeBase>(`/api/knowledge-bases/${id}`),
  update: (id: string, data: { name?: string; description?: string }) =>
    api.patch<KnowledgeBase>(`/api/knowledge-bases/${id}`, data),
  remove: (id: string) => api.delete(`/api/knowledge-bases/${id}`),
};

export const documentApi = {
  list: (kbId: string) => api.get<DocumentItem[]>(`/api/knowledge-bases/${kbId}/documents`),
  get: (kbId: string, docId: string) => api.get<DocumentItem>(`/api/knowledge-bases/${kbId}/documents/${docId}`),
  upload: (kbId: string, files: File[]) => {
    const form = new FormData();
    files.forEach((f) => form.append("files", f));
    return api.post<DocumentItem[]>(`/api/knowledge-bases/${kbId}/documents/upload`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  remove: (kbId: string, docId: string) => api.delete(`/api/knowledge-bases/${kbId}/documents/${docId}`),
  content: (kbId: string, docId: string, page?: number) =>
    api.get(`/api/knowledge-bases/${kbId}/documents/${docId}/content`, { params: { page } }),
};

export const searchApi = {
  search: (kbId: string, q: string, filters?: { document_id?: string; file_type?: string }) =>
    api.get(`/api/knowledge-bases/${kbId}/search`, { params: { q, ...filters } }),
};

export const chatApi = {
  send: (data: { knowledge_base_id: string; message: string; conversation_id?: string; document_ids?: string[]; agentic?: boolean }) =>
    api.post<ChatResponse>("/api/chat", data),
  conversations: (kbId?: string) => api.get<Conversation[]>("/api/conversations", { params: { knowledge_base_id: kbId } }),
  messages: (convId: string) => api.get<Message[]>(`/api/conversations/${convId}/messages`),
  rename: (convId: string, title: string) => api.patch(`/api/conversations/${convId}`, null, { params: { title } }),
  remove: (convId: string) => api.delete(`/api/conversations/${convId}`),
};

export const compareApi = {
  compare: (kbId: string, documentIds: string[], focus?: string) =>
    api.post(`/api/knowledge-bases/${kbId}/compare`, { document_ids: documentIds, focus }),
};

export const summarizeApi = {
  summarize: (kbId: string, documentId: string, mode: string, section?: string) =>
    api.post(`/api/knowledge-bases/${kbId}/summarize`, { document_id: documentId, mode, section }),
};

export const questionsApi = {
  generate: (kbId: string, documentId: string, difficulty: string, count: number) =>
    api.post(`/api/knowledge-bases/${kbId}/generate-questions`, { document_id: documentId, difficulty, count }),
};

export const feedbackApi = {
  submit: (messageId: string, feedback: "up" | "down", reason?: string) =>
    api.post("/api/feedback", { message_id: messageId, feedback, reason }),
};

export const dashboardApi = {
  summary: () => api.get<DashboardSummary>("/api/dashboard"),
};

export const analyticsApi = {
  get: () => api.get("/api/analytics"),
};

export const debugApi = {
  retrieve: (kbId: string, q: string) => api.get(`/api/knowledge-bases/${kbId}/debug/retrieve`, { params: { q } }),
  failedQueries: (kbId: string) => api.get(`/api/knowledge-bases/${kbId}/debug/failed-queries`),
};

export const evalApi = {
  addQuestion: (kbId: string, data: any) => api.post(`/api/knowledge-bases/${kbId}/eval/questions`, data),
  listQuestions: (kbId: string) => api.get(`/api/knowledge-bases/${kbId}/eval/questions`),
  deleteQuestion: (kbId: string, qId: string) => api.delete(`/api/knowledge-bases/${kbId}/eval/questions/${qId}`),
  run: (kbId: string, config: Record<string, any>) => api.post(`/api/knowledge-bases/${kbId}/eval/run`, { knowledge_base_id: kbId, config }),
  runs: (kbId: string) => api.get(`/api/knowledge-bases/${kbId}/eval/runs`),
  compareRuns: (kbId: string, a: string, b: string) => api.get(`/api/knowledge-bases/${kbId}/eval/runs/${a}/compare/${b}`),
};
