import { useEffect, useState } from "react";
import { X, FileText } from "lucide-react";
import { documentApi } from "../api/endpoints";
import type { Citation } from "../types";
import { Skeleton } from "./Skeleton";

export default function SourceViewerModal({
  kbId,
  citation,
  onClose,
}: {
  kbId: string;
  citation: Citation;
  onClose: () => void;
}) {
  const [chunks, setChunks] = useState<{ chunk_id: string; page_number: number; section: string; heading: string; text: string }[] | null>(null);

  useEffect(() => {
    setChunks(null);
    documentApi.content(kbId, citation.document_id, citation.page_number).then((res) => setChunks(res.data.chunks));
  }, [kbId, citation.document_id, citation.page_number]);

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 px-4" onClick={onClose}>
      <div
        className="bg-white dark:bg-ink-900 rounded-2xl w-full max-w-2xl max-h-[80vh] flex flex-col border border-ink-200 dark:border-ink-800"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-ink-200 dark:border-ink-800">
          <div className="flex items-center gap-2 min-w-0">
            <FileText size={16} className="text-amber-500 shrink-0" />
            <div className="min-w-0">
              <h3 className="font-semibold text-sm truncate">{citation.filename}</h3>
              <p className="text-xs text-ink-400 font-mono">
                Page {citation.page_number}
                {citation.section ? ` · ${citation.section}` : ""} · relevance {citation.relevance_score.toFixed(2)}
              </p>
            </div>
          </div>
          <button onClick={onClose} className="text-ink-400 hover:text-ink-900 dark:hover:text-ink-50 shrink-0">
            <X size={18} />
          </button>
        </div>

        <div className="p-6 overflow-y-auto space-y-4">
          {chunks === null ? (
            <>
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-5/6" />
              <Skeleton className="h-4 w-2/3" />
            </>
          ) : chunks.length === 0 ? (
            <p className="text-sm text-ink-400">No indexed content found for this page.</p>
          ) : (
            chunks.map((c) => (
              <div
                key={c.chunk_id}
                className={
                  c.chunk_id === citation.chunk_id
                    ? "p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 text-sm leading-relaxed"
                    : "p-3 rounded-lg text-sm leading-relaxed text-ink-500"
                }
              >
                {c.heading && <p className="text-xs font-semibold text-ink-400 mb-1 uppercase tracking-wide">{c.heading}</p>}
                {c.text}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
