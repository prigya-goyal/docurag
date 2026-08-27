import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import clsx from "clsx";
import { kbApi } from "../api/endpoints";
import type { KnowledgeBase } from "../types";
import DocumentsTab from "../components/DocumentsTab";
import ChatTab from "../components/ChatTab";
import CompareTab from "../components/CompareTab";
import SummarizeTab from "../components/SummarizeTab";
import SearchTab from "../components/SearchTab";
import { Skeleton } from "../components/Skeleton";

const TABS = [
  { key: "chat", label: "Ask" },
  { key: "documents", label: "Documents" },
  { key: "search", label: "Search" },
  { key: "compare", label: "Compare" },
  { key: "summarize", label: "Summarize & quiz" },
] as const;

type TabKey = (typeof TABS)[number]["key"];

export default function KnowledgeBaseDetailPage() {
  const { kbId } = useParams<{ kbId: string }>();
  const [kb, setKb] = useState<KnowledgeBase | null>(null);
  const [tab, setTab] = useState<TabKey>("chat");

  useEffect(() => {
    if (kbId) kbApi.get(kbId).then((res) => setKb(res.data));
  }, [kbId]);

  if (!kbId) return null;

  return (
    <div className="p-8 max-w-6xl">
      <Link to="/knowledge-bases" className="inline-flex items-center gap-1.5 text-sm text-ink-400 hover:text-ink-900 dark:hover:text-ink-50 mb-4">
        <ArrowLeft size={14} /> Knowledge bases
      </Link>

      {kb ? (
        <div className="mb-6">
          <h1 className="font-display text-3xl font-semibold text-ink-900 dark:text-ink-50">{kb.name}</h1>
          {kb.description && <p className="text-sm text-ink-400 mt-1">{kb.description}</p>}
        </div>
      ) : (
        <Skeleton className="h-10 w-64 mb-6" />
      )}

      <div className="flex gap-1 border-b border-ink-200 dark:border-ink-800 mb-6">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={clsx(
              "px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors",
              tab === t.key
                ? "border-amber-500 text-ink-900 dark:text-ink-50"
                : "border-transparent text-ink-400 hover:text-ink-700 dark:hover:text-ink-200"
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "chat" && <ChatTab kbId={kbId} />}
      {tab === "documents" && <DocumentsTab kbId={kbId} />}
      {tab === "search" && <SearchTab kbId={kbId} />}
      {tab === "compare" && <CompareTab kbId={kbId} />}
      {tab === "summarize" && <SummarizeTab kbId={kbId} />}
    </div>
  );
}
