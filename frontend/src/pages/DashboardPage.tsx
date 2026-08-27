import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Library, FileText, Layers, MessageSquare, Gauge, ArrowRight } from "lucide-react";
import { dashboardApi } from "../api/endpoints";
import type { DashboardSummary } from "../types";
import { Skeleton } from "../components/Skeleton";

const statCards = [
  { key: "knowledge_bases", label: "Knowledge bases", icon: Library },
  { key: "documents", label: "Documents", icon: FileText },
  { key: "pages", label: "Total pages", icon: FileText },
  { key: "indexed_chunks", label: "Indexed chunks", icon: Layers },
  { key: "questions_asked", label: "Questions asked", icon: MessageSquare },
] as const;

export default function DashboardPage() {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    dashboardApi
      .summary()
      .then((res) => setData(res.data))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-8 max-w-6xl">
      <div className="mb-8">
        <h1 className="font-display text-3xl font-semibold text-ink-900 dark:text-ink-50">Dashboard</h1>
        <p className="text-sm text-ink-400 mt-1">Upload your knowledge. Ask questions. Get grounded answers.</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
        {loading
          ? Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-24 rounded-xl" />)
          : statCards.map((s) => (
              <div key={s.key} className="rounded-xl border border-ink-200 dark:border-ink-800 bg-white dark:bg-ink-900 p-4">
                <s.icon size={16} className="text-ink-400 mb-3" />
                <p className="font-mono text-2xl font-semibold text-ink-900 dark:text-ink-50">
                  {(data?.[s.key] ?? 0).toLocaleString()}
                </p>
                <p className="text-xs text-ink-400 mt-0.5">{s.label}</p>
              </div>
            ))}
      </div>

      <div className="grid md:grid-cols-2 gap-4 mb-8">
        <div className="rounded-xl border border-ink-200 dark:border-ink-800 bg-white dark:bg-ink-900 p-5">
          <div className="flex items-center gap-2 mb-1">
            <Gauge size={16} className="text-teal-500" />
            <h3 className="font-semibold text-sm">RAG performance summary</h3>
          </div>
          <p className="text-xs text-ink-400 mb-4">Average grounding score across all answered questions.</p>
          <p className="font-mono text-3xl font-semibold text-teal-600 dark:text-teal-400">
            {loading ? "—" : (data?.average_retrieval_score ?? 0).toFixed(2)}
          </p>
        </div>

        <div className="rounded-xl border border-ink-200 dark:border-ink-800 bg-white dark:bg-ink-900 p-5">
          <h3 className="font-semibold text-sm mb-4">Processing status</h3>
          {loading ? (
            <Skeleton className="h-16" />
          ) : Object.keys(data?.processing_status ?? {}).length === 0 ? (
            <p className="text-xs text-ink-400">No documents uploaded yet.</p>
          ) : (
            <ul className="space-y-1.5">
              {Object.entries(data!.processing_status).map(([status, count]) => (
                <li key={status} className="flex justify-between text-xs">
                  <span className="text-ink-500 font-mono">{status}</span>
                  <span className="font-medium">{count}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <div className="rounded-xl border border-ink-200 dark:border-ink-800 bg-white dark:bg-ink-900 p-5">
          <h3 className="font-semibold text-sm mb-3">Recent documents</h3>
          {!loading && (data?.recent_documents.length ?? 0) === 0 && (
            <p className="text-xs text-ink-400">Nothing uploaded yet.</p>
          )}
          <ul className="space-y-2">
            {data?.recent_documents.map((d) => (
              <li key={d.id} className="flex items-center justify-between text-sm">
                <span className="truncate">{d.filename}</span>
                <span className="text-xs font-mono text-ink-400 shrink-0 ml-2">{d.status}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="rounded-xl border border-ink-200 dark:border-ink-800 bg-white dark:bg-ink-900 p-5">
          <h3 className="font-semibold text-sm mb-3">Recent conversations</h3>
          {!loading && (data?.recent_conversations.length ?? 0) === 0 && (
            <p className="text-xs text-ink-400">No questions asked yet.</p>
          )}
          <ul className="space-y-2">
            {data?.recent_conversations.map((c) => (
              <li key={c.id} className="text-sm truncate">{c.title}</li>
            ))}
          </ul>
        </div>
      </div>

      <Link
        to="/knowledge-bases"
        className="inline-flex items-center gap-2 mt-8 text-sm font-medium text-amber-600 dark:text-amber-400 hover:underline"
      >
        Go to knowledge bases <ArrowRight size={14} />
      </Link>
    </div>
  );
}
