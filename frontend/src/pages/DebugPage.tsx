import { useEffect, useState } from "react";
import { Bug, Loader2, Search } from "lucide-react";
import { kbApi, debugApi } from "../api/endpoints";
import type { KnowledgeBase } from "../types";
import GroundingBadge from "../components/GroundingBadge";

export default function DebugPage() {
  const [kbs, setKbs] = useState<KnowledgeBase[]>([]);
  const [kbId, setKbId] = useState("");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any | null>(null);

  useEffect(() => {
    kbApi.list().then((res) => {
      setKbs(res.data);
      if (res.data.length) setKbId(res.data[0].id);
    });
  }, []);

  async function runDebug(e: React.FormEvent) {
    e.preventDefault();
    if (!kbId || !query.trim()) return;
    setLoading(true);
    setResult(null);
    try {
      const res = await debugApi.retrieve(kbId, query);
      setResult(res.data);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-8 max-w-6xl">
      <div className="flex items-center gap-2 mb-1">
        <Bug size={20} className="text-teal-500" />
        <h1 className="font-display text-3xl font-semibold text-ink-900 dark:text-ink-50">Retrieval debugger</h1>
      </div>
      <p className="text-sm text-ink-400 mb-6">Inspect exactly why the system produced an answer: candidates, scores, and final context.</p>

      <form onSubmit={runDebug} className="flex gap-2 mb-8">
        <select
          value={kbId}
          onChange={(e) => setKbId(e.target.value)}
          className="px-3 py-2.5 rounded-lg border border-ink-200 dark:border-ink-700 bg-ink-50 dark:bg-ink-800 text-sm outline-none"
        >
          {kbs.map((kb) => (
            <option key={kb.id} value={kb.id}>
              {kb.name}
            </option>
          ))}
        </select>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g. What is the attendance requirement?"
          className="flex-1 px-3 py-2.5 rounded-lg border border-ink-200 dark:border-ink-700 bg-ink-50 dark:bg-ink-800 text-sm outline-none focus:ring-2 focus:ring-amber-500/50"
        />
        <button
          type="submit"
          disabled={loading}
          className="flex items-center gap-2 bg-ink-900 dark:bg-amber-500 text-white dark:text-ink-950 text-sm font-medium px-4 py-2.5 rounded-lg hover:opacity-90"
        >
          {loading ? <Loader2 size={15} className="animate-spin" /> : <Search size={15} />}
          Trace
        </button>
      </form>

      {result && (
        <div className="space-y-6">
          <div className="rounded-xl border border-ink-200 dark:border-ink-800 bg-white dark:bg-ink-900 p-5">
            <p className="text-xs text-ink-400 mb-1">Rewritten query</p>
            <p className="font-mono text-sm mb-4">{result.rewritten_query}</p>
            <p className="text-xs text-ink-400 mb-1">Answer</p>
            <p className="text-sm leading-relaxed mb-3">{result.answer}</p>
            <div className="flex items-center gap-3">
              <GroundingBadge label={result.grounding_label} score={result.grounding_score} />
              <span className="text-xs font-mono text-ink-400">
                retrieval {result.timings_ms.retrieval_ms}ms · rerank {result.timings_ms.rerank_ms}ms · generation{" "}
                {result.timings_ms.generation_ms}ms · total {result.timings_ms.total_ms}ms
              </span>
            </div>
          </div>

          <div className="rounded-xl border border-ink-200 dark:border-ink-800 overflow-hidden">
            <div className="px-5 py-3 border-b border-ink-200 dark:border-ink-800 bg-ink-100 dark:bg-ink-800/60">
              <h3 className="text-sm font-semibold">Retrieved candidates ({result.candidates.length})</h3>
            </div>
            <table className="w-full text-xs">
              <thead className="text-ink-400 uppercase tracking-wide">
                <tr>
                  <th className="text-left px-4 py-2 font-medium">Document</th>
                  <th className="text-left px-4 py-2 font-medium">Page</th>
                  <th className="text-left px-4 py-2 font-medium">Vector</th>
                  <th className="text-left px-4 py-2 font-medium">BM25</th>
                  <th className="text-left px-4 py-2 font-medium">Hybrid</th>
                  <th className="text-left px-4 py-2 font-medium">Reranker</th>
                  <th className="text-left px-4 py-2 font-medium">In context</th>
                </tr>
              </thead>
              <tbody>
                {result.candidates.map((c: any) => (
                  <tr
                    key={c.chunk_id}
                    className={`border-t border-ink-100 dark:border-ink-800 ${c.used_in_context ? "bg-teal-500/5" : ""}`}
                  >
                    <td className="px-4 py-2 truncate max-w-[180px]">{c.filename}</td>
                    <td className="px-4 py-2 font-mono">{c.page_number}</td>
                    <td className="px-4 py-2 font-mono">{c.vector_score.toFixed(3)}</td>
                    <td className="px-4 py-2 font-mono">{c.bm25_score.toFixed(3)}</td>
                    <td className="px-4 py-2 font-mono">{c.hybrid_score.toFixed(3)}</td>
                    <td className="px-4 py-2 font-mono">{c.reranker_score !== null ? c.reranker_score.toFixed(3) : "—"}</td>
                    <td className="px-4 py-2">
                      {c.used_in_context && <span className="text-teal-600 dark:text-teal-400 font-semibold">✓</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
