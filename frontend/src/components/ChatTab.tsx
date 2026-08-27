import { useEffect, useRef, useState } from "react";
import { Send, Loader2, ThumbsUp, ThumbsDown, Plus, Trash2, Sparkles } from "lucide-react";
import toast from "react-hot-toast";
import { chatApi, feedbackApi } from "../api/endpoints";
import type { ChatResponse, Citation, Conversation, Message } from "../types";
import GroundingBadge from "./GroundingBadge";
import AnswerWithCitations from "./AnswerWithCitations";
import SourceViewerModal from "./SourceViewerModal";
import { extractErrorMessage } from "../api/client";

interface DisplayMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: Citation[];
  grounding_label?: string;
  grounding_score?: number;
  latency_ms?: Record<string, number>;
  feedback?: string;
}

const FEEDBACK_REASONS = [
  { value: "incorrect_answer", label: "Incorrect answer" },
  { value: "wrong_source", label: "Wrong source" },
  { value: "missing_information", label: "Missing information" },
  { value: "poor_explanation", label: "Poor explanation" },
  { value: "hallucination", label: "Hallucination" },
];

export default function ChatTab({ kbId }: { kbId: string }) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [agentic, setAgentic] = useState(false);
  const [viewingCitation, setViewingCitation] = useState<Citation | null>(null);
  const [feedbackTarget, setFeedbackTarget] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  function loadConversations() {
    chatApi.conversations(kbId).then((res) => setConversations(res.data));
  }

  useEffect(loadConversations, [kbId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function openConversation(convId: string) {
    setActiveConvId(convId);
    const res = await chatApi.messages(convId);
    setMessages(
      res.data.map((m: Message) => ({
        id: m.id,
        role: m.role,
        content: m.content,
        citations: m.citations || [],
        grounding_label: m.grounding_label,
        grounding_score: m.grounding_score,
        feedback: undefined,
      }))
    );
  }

  function startNewConversation() {
    setActiveConvId(null);
    setMessages([]);
  }

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    const question = input.trim();
    if (!question || sending) return;

    setMessages((prev) => [...prev, { id: `temp-${Date.now()}`, role: "user", content: question, citations: [] }]);
    setInput("");
    setSending(true);

    try {
      const res = await chatApi.send({
        knowledge_base_id: kbId,
        message: question,
        conversation_id: activeConvId ?? undefined,
        agentic,
      });
      const data: ChatResponse = res.data;
      setActiveConvId(data.conversation_id);
      setMessages((prev) => [
        ...prev,
        {
          id: data.message_id,
          role: "assistant",
          content: data.answer,
          citations: data.citations,
          grounding_label: data.grounding_label,
          grounding_score: data.grounding_score,
          latency_ms: data.latency_ms,
        },
      ]);
      loadConversations();
    } catch (err) {
      toast.error(extractErrorMessage(err));
      setMessages((prev) => prev.slice(0, -1));
    } finally {
      setSending(false);
    }
  }

  async function submitFeedback(messageId: string, feedback: "up" | "down", reason?: string) {
    try {
      await feedbackApi.submit(messageId, feedback, reason);
      setMessages((prev) => prev.map((m) => (m.id === messageId ? { ...m, feedback } : m)));
      setFeedbackTarget(null);
      toast.success("Thanks for the feedback");
    } catch (err) {
      toast.error(extractErrorMessage(err));
    }
  }

  async function deleteConversation(convId: string, e: React.MouseEvent) {
    e.stopPropagation();
    await chatApi.remove(convId);
    if (activeConvId === convId) startNewConversation();
    loadConversations();
  }

  return (
    <div className="flex h-[calc(100vh-220px)] min-h-[500px] rounded-xl border border-ink-200 dark:border-ink-800 overflow-hidden">
      <div className="w-56 shrink-0 border-r border-ink-200 dark:border-ink-800 flex flex-col bg-ink-50/50 dark:bg-ink-900/50">
        <button
          onClick={startNewConversation}
          className="flex items-center gap-2 m-3 px-3 py-2 rounded-lg text-sm font-medium bg-white dark:bg-ink-800 border border-ink-200 dark:border-ink-700 hover:border-amber-500/50"
        >
          <Plus size={14} /> New chat
        </button>
        <div className="flex-1 overflow-y-auto px-2 space-y-1">
          {conversations.map((c) => (
            <div
              key={c.id}
              onClick={() => openConversation(c.id)}
              className={`group flex items-center justify-between px-3 py-2 rounded-lg text-xs cursor-pointer ${
                activeConvId === c.id
                  ? "bg-ink-900 text-ink-50 dark:bg-ink-100 dark:text-ink-950"
                  : "hover:bg-ink-100 dark:hover:bg-ink-800 text-ink-500"
              }`}
            >
              <span className="truncate">{c.title}</span>
              <button onClick={(e) => deleteConversation(c.id, e)} className="opacity-0 group-hover:opacity-100 shrink-0 ml-1">
                <Trash2 size={12} />
              </button>
            </div>
          ))}
        </div>
      </div>

      <div className="flex-1 flex flex-col min-w-0">
        <div className="flex-1 overflow-y-auto p-6 space-y-5">
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-center text-ink-400">
              <Sparkles size={22} className="mb-2 text-amber-500" />
              <p className="text-sm">Ask a question about the documents in this knowledge base.</p>
            </div>
          )}

          {messages.map((m) => (
            <div key={m.id} className={m.role === "user" ? "flex justify-end" : ""}>
              {m.role === "user" ? (
                <div className="max-w-[75%] bg-ink-900 dark:bg-ink-800 text-ink-50 rounded-2xl rounded-br-sm px-4 py-2.5 text-sm">
                  {m.content}
                </div>
              ) : (
                <div className="max-w-[85%]">
                  <div className="bg-white dark:bg-ink-900 border border-ink-200 dark:border-ink-800 rounded-2xl rounded-bl-sm px-4 py-3 text-sm">
                    <AnswerWithCitations
                      text={m.content}
                      citations={m.citations}
                      onCitationClick={(c) => setViewingCitation(c)}
                    />
                  </div>
                  <div className="flex items-center gap-3 mt-2 px-1 flex-wrap">
                    {m.grounding_label && <GroundingBadge label={m.grounding_label} score={m.grounding_score} />}
                    {m.citations.length > 0 && (
                      <span className="text-xs text-ink-400">
                        {m.citations.length} source{m.citations.length > 1 ? "s" : ""}
                      </span>
                    )}
                    {m.latency_ms && (
                      <span className="text-xs text-ink-400 font-mono">{m.latency_ms.total_ms}ms</span>
                    )}
                    <div className="flex items-center gap-1 ml-auto">
                      <button
                        onClick={() => submitFeedback(m.id, "up")}
                        className={`p-1 rounded hover:bg-ink-100 dark:hover:bg-ink-800 ${m.feedback === "up" ? "text-teal-500" : "text-ink-400"}`}
                      >
                        <ThumbsUp size={13} />
                      </button>
                      <button
                        onClick={() => setFeedbackTarget(feedbackTarget === m.id ? null : m.id)}
                        className={`p-1 rounded hover:bg-ink-100 dark:hover:bg-ink-800 ${m.feedback === "down" ? "text-rose-500" : "text-ink-400"}`}
                      >
                        <ThumbsDown size={13} />
                      </button>
                    </div>
                  </div>
                  {feedbackTarget === m.id && (
                    <div className="flex flex-wrap gap-1.5 mt-2 px-1">
                      {FEEDBACK_REASONS.map((r) => (
                        <button
                          key={r.value}
                          onClick={() => submitFeedback(m.id, "down", r.value)}
                          className="text-xs px-2 py-1 rounded-full border border-ink-200 dark:border-ink-700 text-ink-500 hover:border-rose-400 hover:text-rose-500"
                        >
                          {r.label}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}

          {sending && (
            <div className="flex items-center gap-2 text-ink-400 text-sm">
              <Loader2 size={14} className="animate-spin" /> Retrieving evidence and generating an answer…
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <form onSubmit={handleSend} className="border-t border-ink-200 dark:border-ink-800 p-3 flex items-end gap-2">
          <label className="flex items-center gap-1.5 text-xs text-ink-400 mb-2.5 shrink-0 cursor-pointer" title="Agentic mode plans and runs multiple searches for complex/comparison questions">
            <input type="checkbox" checked={agentic} onChange={(e) => setAgentic(e.target.checked)} className="accent-amber-500" />
            Agentic
          </label>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend(e as any);
              }
            }}
            rows={1}
            placeholder="Ask a question about your documents…"
            className="flex-1 resize-none px-3 py-2.5 rounded-lg border border-ink-200 dark:border-ink-700 bg-ink-50 dark:bg-ink-800 text-sm outline-none focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500"
          />
          <button
            type="submit"
            disabled={sending || !input.trim()}
            className="bg-ink-900 dark:bg-amber-500 text-white dark:text-ink-950 p-2.5 rounded-lg hover:opacity-90 disabled:opacity-40 shrink-0"
          >
            <Send size={16} />
          </button>
        </form>
      </div>

      {viewingCitation && <SourceViewerModal kbId={kbId} citation={viewingCitation} onClose={() => setViewingCitation(null)} />}
    </div>
  );
}
